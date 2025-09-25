from fastapi import APIRouter

from app.game.game import game_logic
from app.schemas.game import GameResponse, StartGameRequest

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", status_code=201, response_model=GameResponse)
async def start_game(request: StartGameRequest):
    game = await game_logic.prepare_game(room_id=request.room_id)

    return game


@router.get("/{game_id}")
async def get_game():
    pass


@router.patch("/{game_id}/end")
async def end_game():
    pass
