import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.db import get_session_factory
from app.dependencies import Services, get_services
from app.exceptions import (
    InvalidReconnectToken,
    PlayerNotFoundException,
    RoomNotFoundException,
)
from app.game.enums import WebsocketEvents
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
    room_service = services.room_service

    await websocket.accept()

    player = None
    now = datetime.now(timezone.utc)

    if reconnect_token:
        try:
            player = await reconnect_service.handle_reconnect(reconnect_token, now)
            connection_manager.add_connection(player.id, websocket)

            token = await reconnect_service.create_reconnect_token(player.id)

            if not player.room_id:
                payload = (
                    player.id,
                    {
                        "event": WebsocketEvents.PLAYER_RECONNECTED.value,
                        "payload": {"reconnect_token": token, "avatar_id": player.avatar_id, "player_id": player.id},
                    },
                )
                await connection_manager.send_personal_json(*payload)
            else:
                payload = await reconnect_service.build_reconnect_payload(player, token)
                await connection_manager.send_personal_json(*payload)

        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = await player_service.create_player()
        connection_manager.add_connection(player.id, websocket)

        token = await reconnect_service.create_reconnect_token(player.id)

        await connection_manager.send_personal_json(
            player.id,
            {
                "event": WebsocketEvents.PLAYER_CREATED.value,
                "payload": {
                    "player_id": player.id,
                    "reconnect_token": token,
                    "username": player.username,
                    "avatar_id": player.avatar_id,
                },
            },
        )

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
        if player:
            try:
                connection_manager.remove_connection(player.id)
                await reconnect_service.disconnect(player.id)

                if player.room_id:
                    try:
                        room = await room_service.get_room(player.room_id)
                    except RoomNotFoundException:
                        room = None  # type: ignore

                    if room:
                        await connection_manager.broadcast_to_players(
                            [p.id for p in room.players],
                            {
                                "event": WebsocketEvents.PLAYER_DISCONNECTED.value,
                                "payload": {"player_id": player.id, "username": player.username},
                            },
                            exclude_id=player.id,
                        )
            except Exception:
                # swallow to avoid raising from websocket endpoint
                logger.exception("Failed to clean up after disconnect of player %s", player.id)
