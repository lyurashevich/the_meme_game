from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_game_manager
from app.game.game_manager import GameManager
from app.schemas.players import (
    PlayerCardsSchema,
    PlayerCreateSchema,
    PlayerSchema,
    PlayerStateSchema,
)

router = APIRouter(prefix="/player", tags=["players"])


@router.get("/{player_id}/cards", status_code=200, response_model=list[PlayerCardsSchema])
async def get_player_cards(player_id: str, manager: GameManager = Depends(get_game_manager)):
    player = manager.get_player(player_id)
    player_cards = [{"id": card.id, "image_url": card.image_url} for card in player.handed_cards]

    return player_cards


@router.post("/", response_model=PlayerSchema, status_code=201)
async def create_player(data: PlayerCreateSchema, manager: GameManager = Depends(get_game_manager)):
    player = await manager.create_player(name=data.username)
    return player


@router.get("/{player_id}", response_model=PlayerStateSchema, status_code=200)
async def get_player_info(player_id: str, manager: GameManager = Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


@router.patch("/{player_id}", response_model=PlayerSchema, status_code=200)
async def update_player(player_id: str, user: PlayerCreateSchema, manager: GameManager = Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if user.username is not None:
        player.username = user.username

    return player
