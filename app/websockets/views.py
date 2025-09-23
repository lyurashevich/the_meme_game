import json

from fastapi import APIRouter, Depends, HTTPException
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.game.game_manager import GameManager, get_game_manager

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, manager: GameManager = Depends(get_game_manager)):
    await websocket.accept()

    player = await manager.create_player(websocket)

    await websocket.send_json({"event": "player_created", "player_id": player.id})

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("event") == "chat_message":
                await manager.send_chat_message(
                    room_id=message_data["room_id"], player_id=player.id, message=message_data["message"]
                )
            else:
                await websocket.send_text(f"echo: {data}")

    except WebSocketDisconnect:
        await manager.disconnect(player.id)


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, manager: GameManager = Depends(get_game_manager)):
    room = manager.active_rooms.get("room_id")
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room.messages[-50:]
