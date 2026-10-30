from fastapi import APIRouter, Depends

from app.dependencies import get_game_service
from app.schemas.game import GameScore, GameSettingsSchema
from app.services.game_service import GameService

router = APIRouter(prefix="/api/game", tags=["game"])


@router.get("/{room_id}/score", response_model=list[GameScore])
async def get_game_score(room_id: str, game_service: GameService = Depends(get_game_service)):
    return await game_service.get_game_score(room_id)


@router.get("/{room_id}/game_settings", response_model=GameSettingsSchema)
async def get_game_settings(room_id: str, game_service: GameService = Depends(get_game_service)):
    settings = await game_service.get_game_settings(room_id)
    return GameSettingsSchema.model_validate(settings)
