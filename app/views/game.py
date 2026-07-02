from fastapi import APIRouter, Depends

from app.dependencies import (
    get_connection_manager,
    get_game_manager,
    get_websocket_sender,
)
from app.game.connection_manager import ConnectionManager
from app.game.enums import WebsocketEvents
from app.game.game import game_logic
from app.game.game_manager import GameManager
from app.game.websocket_sender import WebSocketSender
from app.schemas.game import (
    GameResponse,
    GameScore,
    SelectPlayerCardRequest,
    SelectWinnerRequest,
    StartGameRequest,
)

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", status_code=201, response_model=GameResponse)
async def start_game(request: StartGameRequest, sender: WebSocketSender = Depends(get_websocket_sender)):
    game = await game_logic.prepare_game(room_id=request.room_id)
    await game_logic.start_first_round(room_id=request.room_id)

    if game is None:
        return

    await sender.send_first_round_started(game)

    return game


@router.get("/{room_id}/score", response_model=list[GameScore])
async def get_game_score(room_id: str, game_manager: GameManager = Depends(get_game_manager)):
    return await game_manager.get_game_score(room_id)


@router.patch("/{room_id}/end")
async def end_game():
    pass


@router.patch("/{room_id}/players_choice")
async def players_cards(
    room_id: str,
    data: SelectPlayerCardRequest,
    manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
):
    await game_logic.player_select_card(room_id, player_id=data.player_id, card_id=data.card_id)
    async with manager.get_room_lock(room_id):
        room = manager.get_room(room_id)
        game = manager.get_game(room_id)

        if not game.current_round:
            return

        choice = game.current_round.player_choices[data.player_id]

        payload = {
            "event": WebsocketEvents.PLAYER_SELECTED_CARD.value,
            "card_id": choice.id,
            "image_url": choice.image_url,
        }
        await connection_manager.broadcast_to_room([player.id for player in room.players], payload)


@router.patch("/{room_id}/select_winner")
async def select_winner(room_id: str, data: SelectWinnerRequest):
    await game_logic.leader_choose_winner(room_id, card_id=data.card_id)
