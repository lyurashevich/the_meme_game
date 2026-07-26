from fastapi import APIRouter, Depends

from app.dependencies import get_game_service
from app.schemas.round import GameRoundInfoSchema
from app.services.game_service import GameService

router = APIRouter(prefix="/round", tags=["rounds"])


@router.get("/{room_id}/current", status_code=200, response_model=GameRoundInfoSchema)
async def get_game_round_info(
    room_id: str,
    game_service: GameService = Depends(get_game_service),
):
    return await game_service.get_current_round(room_id)
