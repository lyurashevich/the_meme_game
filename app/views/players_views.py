from fastapi import APIRouter, Depends, HTTPException

from app.game.dataclasses import Player
from app.game.game_manager import get_game_manager
from app.schemas.players import (PlayerCreateSchema, PlayerSchema,
                                 PlayerStateSchema)

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/", response_model=PlayerSchema, status_code=201)
async def create_user(data: PlayerCreateSchema, manager=Depends(get_game_manager)):
    player = Player(username=data.username)
    manager.players[player.id] = player
    return player


@router.get("/{player_id}", response_model=PlayerStateSchema, status_code=200)
async def get_player_info(player_id: str, manager=Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


@router.patch("/{player_id}", response_model=PlayerSchema, status_code=200)
async def update_user(player_id: str, user: PlayerCreateSchema, manager=Depends(get_game_manager)):
    player = manager.players.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if user.username is not None:
        player.username = user.username

    return player
