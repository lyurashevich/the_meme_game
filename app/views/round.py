from fastapi import APIRouter, Depends

from app.game.game_manager import GameManager, get_game_manager
from app.schemas.round import GameRoundInfoSchema

router = APIRouter(prefix="/round", tags=["rounds"])


@router.get("/{room_id}/current", status_code=200, response_model=GameRoundInfoSchema)
async def get_game_round_info(room_id: str, manager: GameManager = Depends(get_game_manager)):
    async with manager.get_room_lock(room_id):
        game = manager.get_game(room_id)
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
