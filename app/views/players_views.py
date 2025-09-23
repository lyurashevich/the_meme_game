from fastapi import APIRouter, Depends, HTTPException

from app.game.game_manager import GameManager, get_game_manager
from app.schemas.players import (PlayerCreateSchema, PlayerSchema,
                                 PlayerStateSchema)

router = APIRouter(prefix="/player", tags=["players"])


@router.post("/", response_model=PlayerSchema, status_code=201)
async def create_player(data: PlayerCreateSchema, manager: GameManager = Depends(get_game_manager)):
    player = await manager.create_player(name=data.username)
    return player


@router.get("/{player_id}", response_model=PlayerStateSchema, status_code=200)
async def get_player_info(player_id: str, manager=Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


@router.patch("/{player_id}", response_model=PlayerSchema, status_code=200)
async def update_player(player_id: str, user: PlayerCreateSchema, manager=Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if user.username is not None:
        player.username = user.username

    return player
