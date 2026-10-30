"""A game only starts if every player can get a full hand and there is a situation to play.

Before: the start only checked that there were at least as many memes as players. With
10 memes for 4 players the game started with hands of 6, 4, 0 and 0 cards; and when the
check did fail, the game had already been registered, so the room was left with a game
stuck in "starting" with no round - shown to every player as running.
"""

import asyncio
import json
from unittest.mock import patch

import pytest

from app.exceptions import NotEnoughCardsException
from app.game.enums import GameState
from app.models import MemeCard, SituationCard
from app.services.game_service import CARDS_PER_PLAYER
from app.websockets.dispatcher import ActionContext
from app.websockets.handlers import dispatcher
from tests.helpers import last_room_state


@pytest.fixture
def add_cards(db_session):
    async def add_cards(memes, situations):
        db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(memes)])
        db_session.add_all([SituationCard(text=f"situation {i}") for i in range(situations)])
        await db_session.commit()

    return add_cards


@pytest.fixture
def start_game(test_room_with_players, services, session_factory):
    """The owner sends start_game, exactly as from the client; returns the reply."""

    async def start_game():
        room = test_room_with_players
        ctx = ActionContext(player=room.owner, services=services, session_factory=session_factory)
        return await dispatcher.dispatch(ctx, json.dumps({"event": "start_game", "request_id": "r"}))

    return start_game


def assert_room_untouched(room, services_game):
    assert services_game is None  # no game registered: the room is still in the lobby
    assert all(player.hand_cards == [] for player in room.players)


class TestStartRequiresEnoughCards:
    async def test_too_few_memes_for_full_hands(self, test_room_with_players, start_game, add_cards, game_manager):
        await add_cards(memes=10, situations=5)  # 4 players need 24

        reply = await start_game()

        assert reply["event"] == "error"
        assert reply["payload"]["code"] == "not_enough_cards"
        assert "need at least 24 memes" in reply["payload"]["message"]
        assert "there are 10 memes" in reply["payload"]["message"]
        assert_room_untouched(test_room_with_players, await game_manager.games.get(test_room_with_players.id))

    async def test_no_situations(self, test_room_with_players, start_game, add_cards, game_manager):
        await add_cards(memes=30, situations=0)

        reply = await start_game()

        assert reply["payload"]["code"] == "not_enough_cards"
        assert "0 situations" in reply["payload"]["message"]
        assert_room_untouched(test_room_with_players, await game_manager.games.get(test_room_with_players.id))

    async def test_exactly_enough_cards(self, test_room_with_players, start_game, add_cards, game_manager, outbox):
        players = test_room_with_players.players
        await add_cards(memes=CARDS_PER_PLAYER * len(players), situations=1)

        reply = await start_game()

        assert reply["event"] == "ack", reply
        game = await game_manager.get_game(test_room_with_players.id)
        assert game.state == GameState.ACTIVE
        for player in players:
            assert len(player.hand_cards) == CARDS_PER_PLAYER
            assert len(last_room_state(outbox, player.id)["game"]["my_hand"]) == CARDS_PER_PLAYER
        game_manager.clear_room_tasks(test_room_with_players.id)

    async def test_failed_start_can_be_retried_once_cards_are_added(
        self, test_room_with_players, start_game, add_cards, game_manager
    ):
        await add_cards(memes=10, situations=5)
        assert (await start_game())["event"] == "error"

        await add_cards(memes=20, situations=0)

        assert (await start_game())["event"] == "ack"
        game_manager.clear_room_tasks(test_room_with_players.id)


class TestStartIsAllOrNothing:
    async def test_first_round_failure_leaves_no_game_behind(
        self, test_room_with_players, start_game, add_cards, game_service, game_manager
    ):
        await add_cards(memes=30, situations=5)

        with patch.object(game_service, "_start_first_round_locked", side_effect=RuntimeError("boom")):
            reply = await start_game()

        assert reply["payload"]["code"] == "internal_error"
        assert await game_manager.games.get(test_room_with_players.id) is None

    async def test_initial_deal_never_hands_out_partial_hands(self, prepared_game, game_service):
        prepared_game.meme_deck[:] = prepared_game.meme_deck[: CARDS_PER_PLAYER * len(prepared_game.room.players) - 1]

        with pytest.raises(NotEnoughCardsException):
            await game_service._hand_out_initial_cards(prepared_game)

        assert all(player.hand_cards == [] for player in prepared_game.room.players)


class TestStartWhileGameRunning:
    """Before: starting again during a game silently replaced it - everyone's hand grew to 12
    cards, scores carried over and played cards vanished - and a double click started the
    game twice."""

    async def test_cannot_start_during_a_game(
        self, test_room_with_players, start_game, add_cards, game_service, game_manager
    ):
        await add_cards(memes=60, situations=10)
        assert (await start_game())["event"] == "ack"
        game = await game_manager.get_game(test_room_with_players.id)
        player = test_room_with_players.players[1]
        played = player.hand_cards[0]
        await game_service.player_select_card(test_room_with_players.id, player.id, played.id)
        player.score = 3

        reply = await start_game()

        assert reply["event"] == "error"
        assert reply["payload"]["code"] == "game_already_started"
        assert await game_manager.get_game(test_room_with_players.id) is game  # the running game is untouched
        assert game.current_round.player_choices[player.id] is played
        assert player.score == 3
        assert [len(p.hand_cards) for p in test_room_with_players.players] == [6, 5, 6, 6]
        game_manager.clear_room_tasks(test_room_with_players.id)

    async def test_new_game_after_the_previous_one_ended(
        self, test_room_with_players, start_game, add_cards, game_service, game_manager
    ):
        await add_cards(memes=60, situations=10)
        await start_game()
        first_game = await game_manager.get_game(test_room_with_players.id)
        test_room_with_players.players[1].score = 3
        await game_service.end_game(test_room_with_players.id, test_room_with_players.owner.id)

        reply = await start_game()

        assert reply["event"] == "ack"
        new_game = await game_manager.get_game(test_room_with_players.id)
        assert new_game is not first_game
        assert new_game.state == GameState.ACTIVE
        assert new_game.current_round.round_number == 1
        assert [len(p.hand_cards) for p in test_room_with_players.players] == [6, 6, 6, 6]
        assert [p.score for p in test_room_with_players.players] == [0, 0, 0, 0]
        game_manager.clear_room_tasks(test_room_with_players.id)

    async def test_double_click_starts_only_once(self, test_room_with_players, start_game, add_cards, game_manager):
        await add_cards(memes=60, situations=10)

        replies = await asyncio.gather(start_game(), start_game())

        outcomes = sorted(reply["payload"].get("code", reply["event"]) for reply in replies)
        assert outcomes == ["ack", "game_already_started"]
        game = await game_manager.get_game(test_room_with_players.id)
        assert game.state == GameState.ACTIVE
        assert [len(p.hand_cards) for p in test_room_with_players.players] == [6, 6, 6, 6]
        game_manager.clear_room_tasks(test_room_with_players.id)
