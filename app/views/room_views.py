from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_room_service
from app.schemas.room import RoomStateSchema
from app.services.room_service import RoomService

router = APIRouter(prefix="/api/room", tags=["room"])


@router.get("/all", response_model=list[RoomStateSchema])
async def get_rooms(room_service: RoomService = Depends(get_room_service)):
    return await room_service.get_rooms_list()


@router.get("/{room_id}", response_model=RoomStateSchema)
async def get_room(room_id: str, room_service: RoomService = Depends(get_room_service)):
    if not room_id:
        raise HTTPException(status_code=400, detail="Room id is required")

    room = await room_service.get_room(room_id)

    return room


@router.get("/{room_id}/messages")
async def get_room_messages(
    room_id: str,
    room_service: RoomService = Depends(get_room_service),
):
    room = await room_service.get_room(room_id)

    return room.messages[-50:]
