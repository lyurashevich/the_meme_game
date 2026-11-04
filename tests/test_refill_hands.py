"""Between rounds every hand is filled up to CARDS_PER_PLAYER again, and no further.

Before: everyone except the leader got a card, whether they had played one or not, so a round
in which nobody played (the time ran out) gave those players a 7th card, and an 8th the next time.
"""

import pytest

from app.game.enums import RoundState
from app.services.game_service import CARDS_PER_PLAYER


@pytest.fixture
async def game(prepared_game, game_service):
    await game_service.start_first_round(prepared_game.room_id)
    yield prepared_game
    game_service.game_manager.clear_room_tasks(prepared_game.room_id)


async def time_runs_out(game_service, game):
    """The phase timer of the current phase fires (without waiting for it)."""
    game_service.game_manager.clear_room_tasks(game.room_id)
    await game_service.phase_timer(game.room_id, 0)


def hand_sizes(game):
    return [len(player.hand_cards) for player in game.room.players]


async def test_nobody_played__nobody_gets_a_card(game, game_service):
    deck_before = len(game.meme_deck)

    await time_runs_out(game_service, game)  # the choosing phase ends with no memes played

    assert game.current_round.round_number == 2
    assert hand_sizes(game) == [CARDS_PER_PLAYER] * len(game.room.players)
    assert len(game.meme_deck) == deck_before


async def test_only_those_who_played_get_a_card(game, game_service):
    leader = game.current_round.leader
    player = next(p for p in game.room.players if p is not leader)  # the others don't play
    await game_service.player_select_card(game.room_id, player.id, player.hand_cards[0].id)
    deck_before = len(game.meme_deck)

    await time_runs_out(game_service, game)  # choosing ends: the leader's turn
    assert game.current_round.state == RoundState.LEADER_CHOOSING
    await time_runs_out(game_service, game)  # the leader doesn't choose either

    assert game.current_round.round_number == 2
    assert hand_sizes(game) == [CARDS_PER_PLAYER] * len(game.room.players)
    assert len(game.meme_deck) == deck_before - 1  # one card, for the one who played


async def test_hands_never_grow_past_full_over_many_idle_rounds(game, game_service):
    for _ in range(3):
        await time_runs_out(game_service, game)

    assert game.current_round.round_number == 4
    assert hand_sizes(game) == [CARDS_PER_PLAYER] * len(game.room.players)
