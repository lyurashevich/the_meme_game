import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.dependencies import get_connection_manager, get_game_manager
from app.exceptions import InvalidReconnectToken, PlayerNotFoundException
from app.game.connection_manager import ConnectionManager
from app.game.game_manager import GameManager
from app.game.websocket_sender import WebSocketSender

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    reconnect_token: str | None = None,
    manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    await websocket.accept()

    sender = WebSocketSender(connection_manager)

    player = None
    now = datetime.now(timezone.utc)

    if reconnect_token:
        try:
            player = await manager.handle_reconnect(reconnect_token, now)
            connection_manager.add_connection(player.id, websocket)

            token = await manager.create_reconnect_token(player.id)
            await sender.send(player.id, "player_reconnected", {"room_id": player.room_id, "reconnect_token": token})
            await sender.send_restore_state(player)

            if player.room_id:
                async with manager.get_room_lock(room_id=player.room_id):
                    room = manager.get_room(player.room_id)
                    game = manager.get_game(player.room_id)
                    await sender.send_room_state(room=room, player=player, game=game)

        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = await manager.create_player()
        connection_manager.add_connection(player.id, websocket)

        token = await manager.create_reconnect_token(player.id)

        await sender.send(
            player.id,
            "player_created",
            {
                "player_id": player.id,
                "reconnect_token": token,
            },
        )

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("event") == "chat_message":
                await manager.send_chat_message(
                    room_id=message_data["room_id"],
                    player_id=player.id,
                    message=message_data["message"],
                    connection_manager=connection_manager,
                )
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
                await manager.disconnect(player.id)
            except Exception:  # nosec B110
                # todo: add logging
                # swallow to avoid raising from websocket endpoint
                pass


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, manager: GameManager = Depends(get_game_manager)):
    room = manager.get_room(room_id)

    return room.messages[-50:]
