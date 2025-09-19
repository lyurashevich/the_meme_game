from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from app.game.game_manager import GameManager, get_game_manager
from app.schemas.room import (JoinRoomSchema, RoomCreateSchema,
                              RoomResponseSchema, RoomStateSchema)

router = APIRouter(prefix="/room", tags=["room"])


@router.get("/all", response_model=list[RoomStateSchema], status_code=200)
async def get_rooms(manager: GameManager = Depends(get_game_manager)):
    rooms = list(manager.active_rooms.values())

    return rooms


@router.get("/{room_id}", status_code=200, response_model=RoomStateSchema)
async def get_room(room_id: str, manager: GameManager = Depends(get_game_manager)):
    if not room_id:
        raise HTTPException(status_code=400, detail="Room id is required")

    room = manager.active_rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.post("/", response_model=RoomResponseSchema, status_code=201)
async def create_room(room_data: RoomCreateSchema, manager: GameManager = Depends(get_game_manager)):
    if not room_data.player_id:
        raise HTTPException(status_code=400, detail="Player_id is required")

    player = manager.players.get(room_data.player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    room = await manager.create_room(
        owner=player, room_name=room_data.name, max_players=room_data.max_players, is_private=room_data.is_private
    )

    return room


@router.patch("/{room_id}", status_code=200)
async def join_room(request: JoinRoomSchema, room_id: str, manager: GameManager = Depends(get_game_manager)):
    player = manager.players.get(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    room = manager.active_rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await room.add_player(player)


@router.patch("/{room_id}/leave")
async def leave_room(request: JoinRoomSchema, manager: GameManager = Depends(get_game_manager)):
    await manager.leave_room(request.player_id)
