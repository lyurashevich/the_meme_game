from fastapi import APIRouter, Depends

from app.dependencies import get_player_service
from app.schemas.players import (
    PlayerCardsSchema,
    PlayerCreateSchema,
    PlayerProfileResponseSchema,
    PlayerProfileUpdateSchema,
    PlayerSchema,
)
from app.services.player_service import PlayerService

router = APIRouter(prefix="/player", tags=["players"])


@router.get("/{player_id}/cards", status_code=200, response_model=list[PlayerCardsSchema])
async def get_player_cards(player_id: str, player_service: PlayerService = Depends(get_player_service)):
    cards = player_service.get_player_cards(player_id)
    return cards


@router.post("/", response_model=PlayerSchema, status_code=201)
async def create_player(data: PlayerCreateSchema, player_service: PlayerService = Depends(get_player_service)):
    player = player_service.create_player(username=data.username)
    return player


# @router.get("/{player_id}", response_model=PlayerStateSchema, status_code=200)
# # todo: check if frontend uses this url and switch to a new one
# async def get_player_info(player_id: str, manager: GameManager = Depends(get_game_manager)):
#     player = manager.players.get(player_id)
#     if not player:
#         raise HTTPException(status_code=404, detail="Player not found")
#
#     return player


@router.get("/{player_id}/profile", response_model=PlayerProfileResponseSchema)
async def get_player_profile(player_id: str, player_service: PlayerService = Depends(get_player_service)):
    player = player_service.get_player(player_id)

    return player


# @router.patch("/{player_id}", response_model=PlayerSchema, status_code=200)
# # todo: check if frontend uses this url and switch to a new one
# async def update_player(player_id: str, user: PlayerCreateSchema, manager: GameManager = Depends(get_game_manager)):
#     player = manager.players.get(player_id)
#     if not player:
#         raise HTTPException(status_code=404, detail="Player not found")
#
#     if user.username is not None:
#         player.username = user.username
#
#     return player


@router.patch("/{player_id}/profile", response_model=PlayerProfileResponseSchema)
async def update_player_profile(
    player_id: str, data: PlayerProfileUpdateSchema, player_service: PlayerService = Depends(get_player_service)
):
    player = await player_service.update_player_profile(player_id, data)
    return player
