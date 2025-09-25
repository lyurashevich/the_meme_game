from fastapi import APIRouter, Depends

from app.game.game import game_logic
from app.game.game_manager import GameManager, get_game_manager
from app.schemas.round import GameRoundInfoSchema, StartNewRoundResponseSchema

router = APIRouter(prefix="/round", tags=["rounds"])


@router.post("/{room_id}/start", status_code=201, response_model=StartNewRoundResponseSchema)
async def start_first_round(room_id: str, manager: GameManager = Depends(get_game_manager)):
    game = await manager.get_game(room_id=room_id)

    game_round = await game_logic.start_first_round(game)

    return game_round


@router.get("/{room_id}/current", status_code=200, response_model=GameRoundInfoSchema)
async def get_game_round_info(room_id: str, manager: GameManager = Depends(get_game_manager)):
    game = await manager.get_game(room_id)
    game_round = game.current_round
    if not game_round:
        raise Exception("Round not found")

    return game_round


@router.patch("/{room_id}/{round_number}/end")
async def end_round():
    pass


@router.post("/{room_id}/{round_number}/start")
async def start_new_round():
    pass
