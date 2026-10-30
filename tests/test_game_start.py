"""A game only starts if every player can get a full hand and there is a situation to play.

Before: the start only checked that there were at least as many memes as players. With
10 memes for 4 players the game started with hands of 6, 4, 0 and 0 cards; and when the
check did fail, the game had already been registered, so the room was left with a game
stuck in "starting" with no round - shown to every player as running.
"""

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

        with patch.object(game_service, "start_first_round", side_effect=RuntimeError("boom")):
            reply = await start_game()

        assert reply["payload"]["code"] == "internal_error"
        assert await game_manager.games.get(test_room_with_players.id) is None

    async def test_initial_deal_never_hands_out_partial_hands(self, prepared_game, game_service):
        prepared_game.meme_deck[:] = prepared_game.meme_deck[: CARDS_PER_PLAYER * len(prepared_game.room.players) - 1]

        with pytest.raises(NotEnoughCardsException):
            await game_service._hand_out_initial_cards(prepared_game)

        assert all(player.hand_cards == [] for player in prepared_game.room.players)
