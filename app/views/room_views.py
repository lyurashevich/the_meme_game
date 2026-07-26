from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from app.dependencies import (
    get_connection_manager,
    get_game_manager,
    get_game_service,
    get_player_service,
    get_room_service,
)
from app.game.connection_manager import ConnectionManager
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.schemas.room import (
    JoinRoomSchema,
    LeaveRoomResponseSchema,
    LeaveRoomSchema,
    RoomCreateSchema,
    RoomResponseSchema,
    RoomStateSchema,
)
from app.services.game_service import GameService
from app.services.player_service import PlayerService
from app.services.room_service import RoomService

router = APIRouter(prefix="/room", tags=["room"])


@router.get("/all", response_model=list[RoomResponseSchema])
async def get_rooms(room_service: RoomService = Depends(get_room_service)):
    return room_service.get_rooms_list()


@router.get("/{room_id}", response_model=RoomStateSchema)
async def get_room(room_id: str, room_service: RoomService = Depends(get_room_service)):
    if not room_id:
        raise HTTPException(status_code=400, detail="Room id is required")

    room = room_service.get_room(room_id)

    return room


@router.post("/", response_model=RoomResponseSchema, status_code=201)
async def create_room(
    data: RoomCreateSchema,
    game_manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    room_service: RoomService = Depends(get_room_service),
    player_service: PlayerService = Depends(get_player_service),
):

    player = player_service.get_player(player_id=data.player_id)

    game_manager.validate_player_can_join_room(player.id)

    room = await room_service.create_room(
        owner=player,
        room_name=data.name,
        max_players=data.max_players,
        is_private=data.is_private,
    )

    game_manager.add_player_connection(data.player_id, room.id)

    audience = list(set(connection_manager.player_sockets) - game_manager.players_in_rooms)

    await connection_manager.broadcast_to_players(
        audience,
        {
            "event": WebsocketEvents.ROOM_CREATED.value,
            "payload": {"room_id": room.id, "room_name": room.name},
        },
    )

    return room


@router.patch("/{room_id}")
async def join_room(
    request: JoinRoomSchema,
    room_id: str,
    game_manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    room_service: RoomService = Depends(get_room_service),
    player_service: PlayerService = Depends(get_player_service),
):
    player = player_service.get_player(request.player_id)

    await room_service.join_room(room_id, player)
    room = room_service.get_room(room_id)

    game_manager.add_player_connection(player.id, room.id)
    player_service.add_player(player.id)

    await connection_manager.send_personal_json(
        player.id,
        {
            "event": WebsocketEvents.YOU_JOINED_THE_ROOM.value,
            "payload": {
                "room_id": room.id,
                "room_name": room.name,
                "players": [{"id": p.id, "username": p.username} for p in room.players],
            },
        },
    )

    await connection_manager.broadcast_to_players(
        [player.id for player in room.players],
        {
            "event": WebsocketEvents.PLAYER_JOINED_ROOM.value,
            "payload": {"player_id": player.id, "username": player.username},
        },
        exclude_id=player.id,
    )


@router.patch("/{room_id}/leave", response_model=LeaveRoomResponseSchema)
async def leave_room(
    room_id: str,
    request: LeaveRoomSchema,
    player_service: PlayerService = Depends(get_player_service),
    game_service: GameService = Depends(get_game_service),
):
    player = player_service.get_player(request.player_id)

    return await game_service.process_leave(player, room_id, request.confirm)


@router.get("/{room_id}/messages")
async def get_room_messages(
    room_id: str,
    room_service: RoomService = Depends(get_room_service),
):
    room = room_service.get_room(room_id)

    return room.messages
