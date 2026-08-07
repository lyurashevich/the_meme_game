from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import (
    get_connection_manager,
    get_game_service,
)
from app.game.connection_manager import ConnectionManager
from app.schemas.game import (
    EndGameRequest,
    GameResponse,
    GameScore,
    GameSettingsSchema,
    SelectPlayerCardRequest,
    SelectWinnerRequest,
    StartGameRequest,
    UpdateGameSettingsRequest,
)
from app.services.game_service import GameService

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", status_code=201, response_model=GameResponse)
async def start_game(
    request: StartGameRequest,
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    game_service: GameService = Depends(get_game_service),
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.prepare_game(room_id=request.room_id, db=db)
    await game_service.start_first_round(room_id=request.room_id)

    if game is None:
        return

    for recipients, payload in game_service.build_game_started_messages(game):
        await connection_manager.broadcast_to_players(recipients, payload)

    return game


@router.get("/{room_id}/score", response_model=list[GameScore])
async def get_game_score(room_id: str, game_service: GameService = Depends(get_game_service)):
    return await game_service.get_game_score(room_id)


@router.patch("/{room_id}/end")
async def end_game(
    room_id: str,
    data: EndGameRequest,
    game_service: GameService = Depends(get_game_service),
):
    await game_service.end_game(room_id, data.player_id)


@router.patch("/{room_id}/players_choice")
async def players_cards(
    room_id: str,
    data: SelectPlayerCardRequest,
    game_service: GameService = Depends(get_game_service),
):
    await game_service.player_select_card(room_id, player_id=data.player_id, card_id=data.card_id)


@router.patch("/{room_id}/select_winner")
async def select_winner(
    room_id: str,
    data: SelectWinnerRequest,
    game_service: GameService = Depends(get_game_service),
):
    await game_service.leader_choose_winner(room_id, card_id=data.card_id)


@router.put("/{room_id}/game_settings", response_model=GameSettingsSchema)
async def update_game_settings(
    room_id: str, data: UpdateGameSettingsRequest, game_service: GameService = Depends(get_game_service)
):
    settings = await game_service.change_game_settings(room_id=room_id, player_id=data.player_id, data=data.settings)
    return GameSettingsSchema.model_validate(settings)


@router.get("/{room_id}/game_settings", response_model=GameSettingsSchema)
async def get_game_settings(room_id: str, game_service: GameService = Depends(get_game_service)):
    settings = await game_service.get_game_settings(room_id)
    return GameSettingsSchema.model_validate(settings)
