from fastapi import APIRouter, Depends

from app.dependencies import (
    get_connection_manager,
    get_game_service,
    get_room_service,
)
from app.game.connection_manager import ConnectionManager
from app.game.enums import WebsocketEvents
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
from app.services.room_service import RoomService

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/start", status_code=201, response_model=GameResponse)
async def start_game(
    request: StartGameRequest,
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    game_service: GameService = Depends(get_game_service),
    room_service: RoomService = Depends(get_room_service),
):
    game = await game_service.prepare_game(room_id=request.room_id)
    room = room_service.get_room(request.room_id)
    await game_service.start_first_round(room_id=request.room_id)

    if game is None:
        return

    await connection_manager.broadcast_to_players(
        [player.id for player in room.players],
        {"event": WebsocketEvents.GAME_STARTED.value, "payload": {"room_id": room.id}},
    )

    for player in room.players:
        await connection_manager.send_personal_json(
            player.id,
            {
                "event": WebsocketEvents.ROUND_STARTED.value,
                # "event": WebsocketEvents.GAME_STARTED.value,
                "payload": {
                    "room_id": game.room.id,
                    "leader_id": (game.current_round.leader_id if game and game.current_round else None),
                    "current_round_number": (game.current_round.round_number if game and game.current_round else None),
                    "current_situation_card": (
                        game.current_round.situation_card.to_dict() if game and game.current_round else None
                    ),
                    "score": {player.id: player.score for player in game.room.players},
                    "players": [player.username for player in game.room.players],
                    "player_cards": [card.to_dict() for card in player.handed_cards],
                },
            },
        )

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
