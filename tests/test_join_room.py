"""Who may join a room: there must be space, no game running, and the name must be free.

Before: a full room answered with internal_error (a bare Exception), a player could
join a running game with no cards (and then every round waited for their card until
the timer ran out), and two players could share a name in one room.
"""

import asyncio
import json

import pytest

from app.models import MemeCard, SituationCard
from app.websockets.dispatcher import ActionContext
from app.websockets.handlers import dispatcher


@pytest.fixture
def act(services, session_factory):
    async def act(player, event, payload=None):
        ctx = ActionContext(player=player, services=services, session_factory=session_factory)
        return await dispatcher.dispatch(ctx, json.dumps({"event": event, "request_id": "r", "payload": payload or {}}))

    return act


@pytest.fixture
def new_player(player_service):
    async def new_player(username):
        return await player_service.create_player(username=username)

    return new_player


def error_code(reply):
    assert reply["event"] == "error", reply
    return reply["payload"]["code"]


@pytest.fixture
async def cards_in_db(db_session):
    db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(60)])
    db_session.add_all([SituationCard(text=f"situation {i}") for i in range(10)])
    await db_session.commit()


class TestJoinRules:
    async def test_full_room(self, act, new_player, room_service):
        room = await room_service.create_room(owner=await new_player("Owner"), max_players=3)
        for name in ("A", "B"):
            assert (await act(await new_player(name), "join_room", {"room_id": room.id}))["event"] == "ack"
        late = await new_player("C")

        assert error_code(await act(late, "join_room", {"room_id": room.id})) == "room_is_full"
        assert late not in room.players
        assert late.room_id is None

    async def test_running_game(self, act, new_player, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        late = await new_player("Late")

        assert error_code(await act(late, "join_room", {"room_id": prepared_game.room_id})) == "game_already_started"
        assert late not in prepared_game.room.players
        assert late.room_id is None
        game_service.game_manager.clear_room_tasks(prepared_game.room_id)

    async def test_after_the_game_ended(self, act, new_player, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        await game_service.end_game(prepared_game.room_id, prepared_game.room.owner_id)
        late = await new_player("Late")

        assert (await act(late, "join_room", {"room_id": prepared_game.room_id}))["event"] == "ack"
        assert late in prepared_game.room.players

    @pytest.mark.parametrize("name", ["Neo", "neo", "NEO"])
    async def test_name_taken_in_the_room(self, act, new_player, room_service, name):
        room = await room_service.create_room(owner=await new_player("Neo"))
        twin = await new_player(name)

        assert error_code(await act(twin, "join_room", {"room_id": room.id})) == "username_taken"
        assert twin not in room.players

    async def test_same_name_in_another_room_is_fine(self, act, new_player, room_service):
        await room_service.create_room(owner=await new_player("Neo"))
        other_room = await room_service.create_room(owner=await new_player("Trinity"))

        assert (await act(await new_player("Neo"), "join_room", {"room_id": other_room.id}))["event"] == "ack"


class TestRenameInRoom:
    async def test_cannot_take_a_name_used_in_the_room(self, act, new_player, room_service):
        room = await room_service.create_room(owner=await new_player("Neo"))
        player = await new_player("Trinity")
        await act(player, "join_room", {"room_id": room.id})

        assert error_code(await act(player, "update_profile", {"username": "NEO"})) == "username_taken"
        assert player.username == "Trinity"

    async def test_can_change_the_case_of_own_name(self, act, new_player, room_service):
        owner = await new_player("Neo")
        await room_service.create_room(owner=owner)

        assert (await act(owner, "update_profile", {"username": "NEO"}))["event"] == "ack"
        assert owner.username == "NEO"

    async def test_outside_a_room_any_name_goes(self, act, new_player, room_service):
        await room_service.create_room(owner=await new_player("Neo"))
        browsing = await new_player("Trinity")

        assert (await act(browsing, "update_profile", {"username": "Neo"}))["event"] == "ack"


class TestJoinVersusStart:
    async def test_join_racing_the_start_never_lands_in_the_game_without_cards(
        self, act, test_room_with_players, test_player, new_player, cards_in_db, game_manager
    ):
        late = await new_player("Late")

        start_reply, join_reply = await asyncio.gather(
            act(test_player, "start_game"),
            act(late, "join_room", {"room_id": test_room_with_players.id}),
        )

        assert start_reply["event"] == "ack"
        if join_reply["event"] == "ack":
            assert len(late.hand_cards) == 6  # joined first and was dealt in
        else:
            assert join_reply["payload"]["code"] == "game_already_started"
            assert late not in test_room_with_players.players
        game_manager.clear_room_tasks(test_room_with_players.id)
