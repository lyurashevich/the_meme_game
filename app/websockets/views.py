import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.exceptions import InvalidReconnectToken, PlayerNotFoundException
from app.game.game_manager import GameManager, get_game_manager
from app.game.websocket_sender import WebSocketSender

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket, reconnect_token: str | None = None, manager: GameManager = Depends(get_game_manager)
):
    await websocket.accept()

    sender = WebSocketSender(manager)

    player = None
    now = datetime.now(timezone.utc)

    if reconnect_token:
        try:
            player = await manager.handle_reconnect(websocket, reconnect_token, now)
            token = await manager.create_reconnect_token(player.id)
            await sender.send(player.id, "player_reconnected", {"room_id": player.room_id, "reconnect_token": token})
            await sender.send_restore_state(player)

            if player.room_id:
                await sender.send_room_state(room_id=player.room_id, player=player)

        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = await manager.create_player(websocket)
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
                await manager.disconnect(player.id)
            except Exception:  # nosec B110
                # todo: add logging
                # swallow to avoid raising from websocket endpoint
                pass


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, manager: GameManager = Depends(get_game_manager)):
    room = manager.get_room(room_id)

    return room.messages[-50:]
