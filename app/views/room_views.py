from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from app.dependencies import (
    get_connection_manager,
    get_game_manager,
    get_websocket_sender,
)
from app.game.connection_manager import ConnectionManager
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.game.websocket_sender import WebSocketSender
from app.schemas.room import (
    JoinRoomSchema,
    RoomCreateSchema,
    RoomResponseSchema,
    RoomStateSchema,
)

router = APIRouter(prefix="/room", tags=["room"])


@router.get("/all", response_model=list[RoomResponseSchema], status_code=200)
async def get_rooms(game_manager: GameManager = Depends(get_game_manager)):
    rooms = list(game_manager.active_rooms.values())

    return rooms


@router.get("/{room_id}", status_code=200, response_model=RoomStateSchema)
async def get_room(room_id: str, game_manager: GameManager = Depends(get_game_manager)):
    if not room_id:
        raise HTTPException(status_code=400, detail="Room id is required")

    room = game_manager.get_room(room_id)

    return room


@router.post("/", response_model=RoomResponseSchema, status_code=201)
async def create_room(room_data: RoomCreateSchema, game_manager: GameManager = Depends(get_game_manager)):
    if not room_data.player_id:
        raise HTTPException(status_code=400, detail="Player_id is required")

    player = game_manager.players.get(room_data.player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    room = await game_manager.create_room(
        owner=player,
        room_name=room_data.name,
        max_players=room_data.max_players,
        is_private=room_data.is_private,
    )

    return room


@router.patch("/{room_id}", status_code=200)
async def join_room(
    request: JoinRoomSchema,
    room_id: str,
    game_manager: GameManager = Depends(get_game_manager),
    sender: WebSocketSender = Depends(get_websocket_sender),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    player = game_manager.players.get(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    room = game_manager.active_rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await game_manager.join_room(room_id, player, connection_manager)
    await sender.send(player_id=player.id, event=WebsocketEvents.PLAYER_JOINED_ROOM.value, payload={"room_id": room_id})


@router.patch("/{room_id}/leave")
async def leave_room(
    request: JoinRoomSchema,
    game_manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    await game_manager.leave_room(request.player_id, connection_manager)


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, game_manager: GameManager = Depends(get_game_manager)):
    room = game_manager.get_room(room_id)

    return room.messages
