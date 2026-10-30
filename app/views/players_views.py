from fastapi import APIRouter, Depends

from app.dependencies import get_player_service
from app.schemas.players import BasePlayerProfileResponseSchema
from app.services.player_service import PlayerService

router = APIRouter(prefix="/api/player", tags=["players"])


@router.get("/all", response_model=list[BasePlayerProfileResponseSchema])
async def get_all_players(player_service: PlayerService = Depends(get_player_service)):
    return await player_service.get_players()


@router.get("/{player_id}/profile", response_model=BasePlayerProfileResponseSchema)
async def get_player_profile(player_id: str, player_service: PlayerService = Depends(get_player_service)):
    player = await player_service.get_player(player_id)

    return player
