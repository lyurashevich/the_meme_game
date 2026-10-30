"""Played cards rest in the discard pile for a cooldown, then come back - and never get lost.

Before: the cooldowns didn't match the README (20/30 instead of 10/20), and cards dropped
out of the game for good: a round aborted because its leader left skipped its turn to
return a batch from the pile, a leaving player's hand was thrown away, and so was the
card they had already played in the current round.
"""

import pytest

from app.game.dataclasses import Player
from app.models import MemeCard, SituationCard
from app.services.game_service import (
    MEME_CARDS_COOLDOWN,
    SITUATION_CARDS_COOLDOWN,
    GameService,
)


@pytest.fixture
async def big_game(prepared_game, game_service, player_service):
    """5 players and enough cards for a long game, already in round 1."""
    game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0
    prepared_game.meme_deck.extend(MemeCard(id=1000 + i, image_url=f"http://memes.org/extra/{i}") for i in range(80))
    prepared_game.situation_deck.extend(SituationCard(id=1000 + i, text=f"extra {i}") for i in range(30))

    fifth = Player(username="Fifth")
    await player_service.players.add(fifth)
    prepared_game.room.add_player(fifth)
    fifth.room_id = prepared_game.room_id

    await game_service.start_first_round(prepared_game.room_id)
    yield prepared_game
    game_service.game_manager.clear_room_tasks(prepared_game.room_id)


def memes_in_game(game):
    hands = sum(len(player.hand_cards) for player in game.room.players)
    table = len(game.current_round.player_choices) if game.current_round else 0
    pile = sum(len(batch) for batch in game.meme_discard_pile.values())
    return len(game.meme_deck) + hands + table + pile


async def play_cards(game_service, game, players=None):
    current_round = game.current_round
    for player in players or game.room.players:
        if player is not current_round.leader:
            await game_service.player_select_card(game.room_id, player.id, player.hand_cards[0].id)


async def judge(game_service, game):
    """The leader picks a card; waits until the next round starts."""
    current_round = game.current_round
    card_id = next(iter(current_round.player_choices.values())).id
    await game_service.leader_choose_winner(game.room_id, current_round.leader_id, card_id)
    await game_service.game_manager.room_tasks[game.room_id]["winner_announcement"]


async def play_round(game_service, game):
    await play_cards(game_service, game)
    await judge(game_service, game)


class TestCooldownValues:
    def test_match_the_readme(self):
        assert MEME_CARDS_COOLDOWN == 10
        assert SITUATION_CARDS_COOLDOWN == 20


class TestReturnCooledDownCards:
    def test_returns_batches_once_their_cooldown_is_over(self):
        pile = {1: ["a"], 2: ["b"], 3: ["c"]}
        deck = []

        GameService._return_cooled_down_cards(pile, deck, current_round=12, cooldown=10)

        assert deck == ["a", "b"]  # played in rounds 1 and 2: 10+ rounds ago
        assert pile == {3: ["c"]}

    def test_returns_overdue_batches_skipped_by_an_aborted_round(self):
        pile = {4: ["late"], 5: ["on time"]}
        deck = []

        # round 14 was aborted and never returned batch 4; round 15 brings back both
        GameService._return_cooled_down_cards(pile, deck, current_round=15, cooldown=10)

        assert deck == ["late", "on time"]
        assert pile == {}


class TestMemeCooldownInPlay:
    async def test_played_cards_come_back_after_the_cooldown(self, big_game, game_service):
        await play_cards(game_service, big_game)
        played_in_round_1 = set(big_game.current_round.player_choices.values())
        await judge(game_service, big_game)

        for _ in range(MEME_CARDS_COOLDOWN - 1):  # rounds 2..10
            await play_round(game_service, big_game)
        assert big_game.current_round.round_number == MEME_CARDS_COOLDOWN + 1
        assert not played_in_round_1 & set(big_game.meme_deck)  # still resting

        await play_round(game_service, big_game)  # round 11 ends: round 1's batch is due

        assert played_in_round_1 <= set(big_game.meme_deck) | {
            card for player in big_game.room.players for card in player.hand_cards
        }
        assert 1 not in big_game.meme_discard_pile


class TestNoCardsLost:
    async def test_aborted_round_does_not_strand_cards_in_the_pile(self, big_game, game_service):
        total = memes_in_game(big_game)
        for _ in range(MEME_CARDS_COOLDOWN):
            await play_round(game_service, big_game)

        # the leader of round 11 leaves after everyone played: the round is aborted, never finalized
        await play_cards(game_service, big_game)
        await game_service.process_leave(big_game.current_round.leader, big_game.room_id, confirm=True)
        await play_round(game_service, big_game)  # round 12 ends: batches 1 and 2 are both due

        assert not [r for r in big_game.meme_discard_pile if r <= 12 - MEME_CARDS_COOLDOWN]
        assert memes_in_game(big_game) == total

    async def test_leaving_player_hand_and_played_card_go_back_to_the_deck(self, big_game, game_service):
        total = memes_in_game(big_game)
        leaver = big_game.room.players[2]
        await play_cards(game_service, big_game, players=[leaver])
        played_card = big_game.current_round.player_choices[leaver.id]
        hand = list(leaver.hand_cards)

        await game_service.process_leave(leaver, big_game.room_id, confirm=True)

        assert played_card in big_game.meme_deck
        assert set(hand) <= set(big_game.meme_deck)
        assert memes_in_game(big_game) == total
