from fastapi import APIRouter

from app.game.game import game_logic
from app.schemas.game import GameResponse, SelectPlayerCardRequest, SelectWinnerRequest, StartGameRequest

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", status_code=201, response_model=GameResponse)
async def start_game(request: StartGameRequest):
    game = await game_logic.prepare_game(room_id=request.room_id)

    return game


@router.get("/{room_id}")
async def get_game():
    pass


@router.patch("/{room_id}/end")
async def end_game():
    pass


@router.patch("/{room_id}/players_choice")
async def players_cards(room_id: str, data: SelectPlayerCardRequest):
    await game_logic.player_select_card(room_id, data.player_id, data.card_id)


@router.patch("/{room_id}/select_winner")
async def select_winner(room_id: str, data: SelectWinnerRequest):
    await game_logic.leader_choose_winner(room_id=room_id, winner_player_id=data.winner_id)
