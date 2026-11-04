"""Every phase of a round is timed, and the deadline players see matches the real timer.

Before: only the card-choosing phase had a timer. Once the round moved on to the leader
nothing was timed, so an AFK leader - or a table left empty because nobody played in
time - froze the game forever.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.game.enums import RoundState
from app.services.snapshots import build_room_state


@pytest.fixture
async def started_game(prepared_game, game_service):
    await game_service.start_first_round(prepared_game.room_id)
    yield prepared_game
    game_service.game_manager.clear_room_tasks(prepared_game.room_id)


def phase_timer(game_service, game):
    """The room's running phase timer task, if any."""
    task = game_service.game_manager.room_tasks.get(game.room_id, {}).get("phase_timer")
    return task if task and not task.done() else None


def assert_deadline_in(game, seconds):
    remaining = game.current_round.phase_ends_at - datetime.now(timezone.utc)
    assert timedelta(seconds=seconds - 2) < remaining <= timedelta(seconds=seconds)


async def play_all_cards(game_service, game):
    for player in game.room.players:
        if player is not game.current_round.leader:
            await game_service.player_select_card(game.room_id, player.id, player.hand_cards[0].id)


class TestPhaseTimers:
    async def test_choosing_phase_deadline_matches_round_time_limit(self, started_game, game_service):
        assert started_game.current_round.state == RoundState.CHOOSING_CARDS
        assert phase_timer(game_service, started_game)
        assert_deadline_in(started_game, started_game.settings.round_time_limit)

    async def test_leader_gets_own_timer_when_everyone_played(self, started_game, game_service):
        await play_all_cards(game_service, started_game)

        assert started_game.current_round.state == RoundState.LEADER_CHOOSING
        assert phase_timer(game_service, started_game)
        assert_deadline_in(started_game, game_service.LEADER_TIME_LIMIT_SECONDS)

    async def test_leader_timeout_ends_round_without_winner(self, started_game, game_service):
        game_service.LEADER_TIME_LIMIT_SECONDS = 0
        await play_all_cards(game_service, started_game)

        await phase_timer(game_service, started_game)

        assert started_game.current_round.round_number == 2
        assert started_game.current_round.state == RoundState.CHOOSING_CARDS
        assert all(player.score == 0 for player in started_game.room.players)

    async def test_choosing_timeout_with_cards_moves_to_timed_leader_phase(self, started_game, game_service):
        player = started_game.room.players[1]
        await game_service.player_select_card(started_game.room_id, player.id, player.hand_cards[0].id)

        await game_service.phase_timer(started_game.room_id, timeout=0)

        assert started_game.current_round.state == RoundState.LEADER_CHOOSING
        assert phase_timer(game_service, started_game)
        assert_deadline_in(started_game, game_service.LEADER_TIME_LIMIT_SECONDS)

    async def test_choosing_timeout_without_cards_skips_to_next_round(self, started_game, game_service):
        await game_service.phase_timer(started_game.room_id, timeout=0)

        assert started_game.current_round.round_number == 2
        assert started_game.current_round.state == RoundState.CHOOSING_CARDS
        assert phase_timer(game_service, started_game)

    async def test_choosing_winner_stops_the_leader_timer(self, started_game, game_service):
        await play_all_cards(game_service, started_game)
        winner = started_game.room.players[2]
        card_id = started_game.current_round.player_choices[winner.id].id

        await game_service.leader_choose_winner(started_game.room_id, started_game.room.owner.id, card_id)

        assert phase_timer(game_service, started_game) is None
        assert started_game.current_round.phase_ends_at is None


class TestDeadlineInSnapshot:
    async def test_snapshot_has_deadline_and_server_time(self, started_game):
        now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        started_game.current_round.phase_ends_at = now + timedelta(seconds=45)

        state = build_room_state(started_game.room, started_game, started_game.room.owner, now=now)

        assert state["server_time"] == "2026-01-01T12:00:00+00:00"
        assert state["game"]["ends_at"] == "2026-01-01T12:00:45+00:00"

    async def test_no_deadline_while_winner_is_shown(self, started_game, game_service):
        await play_all_cards(game_service, started_game)
        winner = started_game.room.players[2]
        card_id = started_game.current_round.player_choices[winner.id].id
        await game_service.leader_choose_winner(started_game.room_id, started_game.room.owner.id, card_id)

        state = build_room_state(started_game.room, started_game, winner)

        assert state["game"]["winner"]["player_id"] == winner.id
        assert state["game"]["ends_at"] is None

    def test_lobby_has_server_time_but_no_game(self, test_room, test_player):
        state = build_room_state(test_room, None, test_player)

        assert datetime.fromisoformat(state["server_time"]).tzinfo is not None
        assert state["game"] is None
