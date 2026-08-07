import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.dependencies import (
    get_connection_manager,
    get_player_service,
    get_reconnect_service,
    get_room_service,
)
from app.exceptions import (
    InvalidReconnectToken,
    PlayerNotFoundException,
    RoomNotFoundException,
)
from app.game.connection_manager import ConnectionManager
from app.game.enums import WebsocketEvents
from app.services.player_service import PlayerService
from app.services.reconnect_service import ReconnectService
from app.services.room_service import RoomService

router = APIRouter(prefix="/ws")


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    reconnect_token: str | None = None,
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    player_service: PlayerService = Depends(get_player_service),
    reconnect_service: ReconnectService = Depends(get_reconnect_service),
    room_service: RoomService = Depends(get_room_service),
):
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
                        "payload": {"reconnect_token": token, "avatar": player.avatar, "player_id": player.id},
                    },
                )
                await connection_manager.send_personal_json(*payload)
            else:
                payload = await reconnect_service.build_reconnect_payload(player, token)
                await connection_manager.send_personal_json(*payload)

        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = player_service.create_player()
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
                    "avatar": player.avatar,
                },
            },
        )

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("event") == "chat_message":
                recipients, message_payload = await room_service.send_chat_message(
                    room_id=message_data["room_id"],
                    player=player,
                    message=message_data["message"],
                )
                await connection_manager.broadcast_to_players(recipients, message_payload)
            else:
                await websocket.send_text(f"echo: {data}")

    except WebSocketDisconnect:
        # normal disconnect
        pass
    except Exception:  # nosec B110
        # todo: add logging
        # ensure we don't leave player marked connected on unexpected errors
        # (logged elsewhere or in future)
        pass
    finally:
        if player:
            try:
                connection_manager.remove_connection(player.id)
                await reconnect_service.disconnect(player.id)

                if player.room_id:
                    try:
                        room = room_service.get_room(player.room_id)
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
            except Exception:  # nosec B110
                # todo: add logging
                # swallow to avoid raising from websocket endpoint
                pass


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, room_service: RoomService = Depends(get_room_service)):
    room = room_service.get_room(room_id)

    return room.messages[-50:]
