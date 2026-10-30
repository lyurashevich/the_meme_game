"""When the decks can't cover another round, the game ends with reason "out_of_cards".

Before: _start_new_round raised inside the background task that finishes a round
(NotEnoughCardsException for an empty deck, IndexError halfway through dealing when
a few cards were left), and the game stayed "active" in a round that had already
ended - frozen for every player, with the error only in the server log.
"""

from unittest.mock import patch

import pytest

from app.exceptions import NotEnoughCardsException
from app.game.enums import GameEndReason, GameState, RoundState
from app.models import MemeCard, SituationCard
from tests.helpers import events_for, last_room_state


@pytest.fixture
def game_service(game_service):
    game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0
    return game_service


async def play_round(game_service, game):
    """Everyone plays a card, the leader picks one; waits until the next round (or the end)."""
    current_round = game.current_round
    for player in game.room.players:
        if player is not current_round.leader:
            await game_service.player_select_card(game.room_id, player.id, player.hand_cards[0].id)

    card_id = next(iter(current_round.player_choices.values())).id
    await game_service.leader_choose_winner(game.room_id, current_round.leader_id, card_id)
    await game_service.game_manager.room_tasks[game.room_id]["winner_announcement"]


async def play_until_game_ends(game_service, game, max_rounds=50):
    for _ in range(max_rounds):
        if game.state == GameState.FINISHED:
            return
        await play_round(game_service, game)
    pytest.fail("the game never ended")


def extra_memes(count):
    return [MemeCard(id=1000 + i, image_url=f"http://memes.org/extra/{i}") for i in range(count)]


def extra_situations(count):
    return [SituationCard(id=1000 + i, text=f"extra situation {i}") for i in range(count)]


def assert_ended_out_of_cards(game, outbox):
    assert game.state == GameState.FINISHED
    assert game.current_round is None
    for player in game.room.players:
        endings = [m["payload"] for m in events_for(outbox, player.id) if m["event"] == "game_ended"]
        assert [ending["reason"] for ending in endings] == [GameEndReason.OUT_OF_CARDS.value]
        assert last_room_state(outbox, player.id)["game"] is None  # back to the lobby


class TestMemeDeckRunsOut:
    # 4 players, 30 memes: 24 dealt at the start, 6 left, 3 dealt after every round,
    # and played cards stay on cooldown much longer than this game lasts

    async def test_empty_deck_ends_the_game(self, prepared_game, game_service, outbox):
        prepared_game.situation_deck.extend(extra_situations(20))
        await game_service.start_first_round(prepared_game.room_id)

        await play_until_game_ends(game_service, prepared_game)

        assert_ended_out_of_cards(prepared_game, outbox)

    async def test_too_few_cards_for_everyone_ends_the_game_without_partial_deal(
        self, prepared_game, game_service, outbox
    ):
        prepared_game.situation_deck.extend(extra_situations(20))
        await game_service.start_first_round(prepared_game.room_id)
        await play_round(game_service, prepared_game)  # 3 cards left: exactly one more deal
        await play_round(game_service, prepared_game)
        prepared_game.meme_deck.extend(extra_memes(1))  # 1 card for 3 players

        await play_round(game_service, prepared_game)

        assert_ended_out_of_cards(prepared_game, outbox)
        # hands are cleared when a game ends, so the untouched last card is the evidence
        assert len(prepared_game.meme_deck) == 1

    async def test_cards_back_from_cooldown_keep_the_game_going(self, prepared_game, game_service):
        prepared_game.situation_deck.extend(extra_situations(20))
        await game_service.start_first_round(prepared_game.room_id)

        # played cards come back after one round instead of twenty
        with patch("app.services.game_service.MEME_CARDS_COOLDOWN", 1):
            for _ in range(6):
                await play_round(game_service, prepared_game)

        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.round_number == 7
        game_service.game_manager.clear_room_tasks(prepared_game.room_id)


class TestSituationDeckRunsOut:
    async def test_last_situation_ends_the_game(self, prepared_game, game_service, outbox):
        prepared_game.meme_deck.extend(extra_memes(100))
        await game_service.start_first_round(prepared_game.room_id)  # 5 situations: rounds 1-5

        for _ in range(4):
            await play_round(game_service, prepared_game)
        assert prepared_game.current_round.round_number == 5
        assert prepared_game.situation_deck == []

        await play_round(game_service, prepared_game)

        assert_ended_out_of_cards(prepared_game, outbox)

    async def test_limit_reached_takes_precedence(self, prepared_game, game_service, outbox):
        prepared_game.meme_deck.extend(extra_memes(100))
        prepared_game.settings.max_rounds = 5
        await game_service.start_first_round(prepared_game.room_id)

        await play_until_game_ends(game_service, prepared_game)

        endings = [
            m["payload"]["reason"]
            for m in events_for(outbox, prepared_game.room.owner.id)
            if m["event"] == "game_ended"
        ]
        assert endings == [GameEndReason.LIMIT_REACHED.value]


class TestHandOutOneCard:
    async def test_checks_before_dealing(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round.state = RoundState.ROUND_ENDED
        prepared_game.meme_deck[:] = extra_memes(1)
        hands_before = {p.id: len(p.hand_cards) for p in prepared_game.room.players}

        with pytest.raises(NotEnoughCardsException):
            await game_service._hand_out_one_card(prepared_game)

        assert {p.id: len(p.hand_cards) for p in prepared_game.room.players} == hands_before
        assert len(prepared_game.meme_deck) == 1
        game_service.game_manager.clear_room_tasks(prepared_game.room_id)
