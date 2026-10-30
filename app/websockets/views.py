import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.db import get_session_factory
from app.dependencies import Services, get_services
from app.exceptions import InvalidReconnectToken, PlayerNotFoundException
from app.websockets.dispatcher import ActionContext
from app.websockets.handlers import dispatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws")


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    reconnect_token: str | None = None,
    services: Services = Depends(get_services),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    connection_manager = services.connection_manager
    player_service = services.player_service
    reconnect_service = services.reconnect_service
    notifier = services.notifier

    await websocket.accept()

    player = None

    if reconnect_token:
        try:
            player = await reconnect_service.handle_reconnect(reconnect_token, datetime.now(timezone.utc))
        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = await player_service.create_player()

    connection_manager.add_connection(player.id, websocket)
    token = await reconnect_service.create_reconnect_token(player.id)

    if player.room_id and await services.room_service.rooms.get(player.room_id) is None:
        player.room_id = None  # the room was removed while the player was away

    # who you are, then where you are: your room (with the chat history) or the room list
    await notifier.send_session(player, token)
    if player.room_id:
        # everyone else in the room sees the player back online
        await notifier.broadcast_room_state(player.room_id, with_chat_for=player.id)
    else:
        await notifier.send_rooms_list(player.id)

    ctx = ActionContext(player=player, services=services, session_factory=session_factory)

    try:
        while True:
            raw_message = await websocket.receive_text()
            reply = await dispatcher.dispatch(ctx, raw_message)
            await websocket.send_json(reply)

    except WebSocketDisconnect:
        # normal disconnect
        pass
    except Exception:
        # the finally block still marks the player as disconnected
        logger.exception("Unhandled error in websocket loop for player %s", player.id)
    finally:
        try:
            # If the player already reconnected on another socket, this one closing changes nothing.
            if connection_manager.remove_connection(player.id, websocket):
                await reconnect_service.disconnect(player.id)

                if player.room_id:
                    # the others see the player go offline
                    await notifier.broadcast_room_state(player.room_id)
        except Exception:
            # swallow to avoid raising from websocket endpoint
            logger.exception("Failed to clean up after disconnect of player %s", player.id)
