"""Turn in-memory game state into the payloads sent to clients.

Pure functions: they only read the objects they are given, so they can be called
at any moment and always describe the state as it is right now.
"""

from datetime import datetime, timezone

from app.game.dataclasses import Game, Player, Room
from app.game.enums import GameState, RoundState
from app.models import MemeCard

CHAT_HISTORY_LIMIT = 50


def build_session(player: Player, reconnect_token: str) -> dict:
    return {
        "player_id": player.id,
        "reconnect_token": reconnect_token,
        "username": player.username,
        "avatar_id": player.avatar_id,
    }


def build_rooms_list(rooms: list[Room], games: dict[str, Game | None]) -> list[dict]:
    """Public rooms for the lobby screen. ``games`` maps room id -> its game, if any."""
    return [
        {
            "id": room.id,
            "name": room.name,
            "owner_name": room.owner.username if room.owner else None,
            "players_count": room.players_count,
            "max_players": room.max_players,
            "round_time_limit": room.settings.round_time_limit,
            "max_rounds": room.settings.max_rounds,  # None: no limit
            "status": "playing" if _is_running(games.get(room.id)) else "waiting",
        }
        for room in rooms
        if not room.is_private
    ]


def build_room_state(
    room: Room, game: Game | None, player: Player, chat: list[dict] | None = None, now: datetime | None = None
) -> dict:
    """Everything ``player`` may see about the room, from their point of view.

    ``chat`` is the message history; it is only included when the client needs it
    (right after joining or reconnecting), since new messages arrive as events.

    ``server_time`` lets the client turn ``game.ends_at`` into a countdown without trusting
    its own clock: remaining = ends_at - server_time, then count down locally.
    """
    settings = room.settings
    state = {
        "server_time": _iso(now or datetime.now(timezone.utc)),
        "room": {
            "id": room.id,
            "name": room.name,
            "owner_id": room.owner.id if room.owner else None,
            "max_players": room.max_players,
            "settings": {
                "round_time_limit": settings.round_time_limit,
                "max_rounds": settings.max_rounds,
                "score_to_win": settings.score_to_win,
            },
        },
        "players": [
            {
                "id": p.id,
                "username": p.username,
                "avatar_id": p.avatar_id,
                "score": p.score,
                "is_connected": p.is_connected,
            }
            for p in room.players
        ],
        "game": _build_game_state(game, player) if _is_running(game) else None,
    }

    if chat is not None:
        state["chat"] = chat[-CHAT_HISTORY_LIMIT:]

    return state


def _is_running(game: Game | None) -> bool:
    return game is not None and game.state != GameState.FINISHED


def _iso(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment else None


def _card(card: MemeCard) -> dict:
    return {"id": card.id, "image_url": card.image_url}


def _build_game_state(game: Game, player: Player) -> dict:
    round_ = game.current_round
    state: dict = {
        "state": game.state.value,
        "my_hand": [_card(card) for card in player.hand_cards],
        "round_number": None,
        "round_state": None,
        "leader_id": None,
        "situation": None,
        "submitted_player_ids": [],
        "my_selected_card_id": None,
        "table": [],
        "winner": None,
        "ends_at": None,
    }
    if round_ is None:
        return state

    my_choice = round_.player_choices.get(player.id)
    state.update(
        {
            "round_number": round_.round_number,
            "round_state": round_.state.value,
            "leader_id": round_.leader_id,
            "situation": {"id": round_.situation_card.id, "text": round_.situation_card.text},
            # who has played already - but not what, until the leader starts judging
            "submitted_player_ids": list(round_.player_choices),
            "my_selected_card_id": my_choice.id if my_choice else None,
            # deadline of the current phase; None while the winning card is being shown
            "ends_at": _iso(round_.phase_ends_at),
        }
    )

    if round_.state != RoundState.CHOOSING_CARDS:
        # Anonymous: no authors, and ordered by card id rather than by submission order,
        # which everyone could match against the order of submitted_player_ids.
        state["table"] = [_card(card) for card in sorted(round_.player_choices.values(), key=lambda card: card.id)]

    if round_.winner:
        winning_card = round_.player_choices.get(round_.winner.id)
        state["winner"] = {"player_id": round_.winner.id, "card_id": winning_card.id if winning_card else None}

    return state


def build_game_ended(room: Room, reason: str, final_scores: dict[str, int]) -> dict:
    best = max(final_scores.values(), default=0)
    winner_ids = [player_id for player_id, score in final_scores.items() if best > 0 and score == best]

    return {"room_id": room.id, "reason": reason, "final_scores": final_scores, "winner_ids": winner_ids}
