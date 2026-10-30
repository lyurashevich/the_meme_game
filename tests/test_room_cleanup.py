"""When the last player leaves, the room goes away together with its game and timers.

Before: RoomService.cleanup_room removed only the room. Its game - finished or not -
stayed in the game repository forever, holding on to the room, players and decks.
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
async def cards_in_db(db_session):
    db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(60)])
    db_session.add_all([SituationCard(text=f"situation {i}") for i in range(10)])
    await db_session.commit()


async def everyone_leaves(act, room):
    for player in list(room.players):
        reply = await act(player, "leave_room", {"confirm": True})
        assert reply["event"] == "ack", reply


async def assert_room_gone(room_id, room_service, game_manager):
    assert await room_service.rooms.get(room_id) is None
    assert await game_manager.games.get(room_id) is None
    assert room_id not in game_manager.room_tasks
    assert room_id not in room_service.room_locks


class TestLastPlayerLeaves:
    async def test_after_a_finished_game(
        self, act, test_room_with_players, test_player, cards_in_db, room_service, game_manager
    ):
        room_id = test_room_with_players.id
        await act(test_player, "start_game")
        await act(test_player, "end_game")

        await everyone_leaves(act, test_room_with_players)

        await assert_room_gone(room_id, room_service, game_manager)

    async def test_in_the_middle_of_a_game(
        self, act, test_room_with_players, test_player, cards_in_db, room_service, game_manager
    ):
        room_id = test_room_with_players.id
        await act(test_player, "start_game")
        player = test_room_with_players.players[1]
        await act(player, "select_card", {"card_id": player.hand_cards[0].id})

        await everyone_leaves(act, test_room_with_players)

        await assert_room_gone(room_id, room_service, game_manager)

    async def test_leftover_timers_are_cancelled(self, act, test_room, test_player, room_service, game_manager):
        timer = asyncio.create_task(asyncio.sleep(60))
        game_manager.add_task(test_room.id, "phase_timer", timer)

        await act(test_player, "leave_room")
        await asyncio.sleep(0)  # let the cancellation land

        assert timer.cancelled()
        await assert_room_gone(test_room.id, room_service, game_manager)

    async def test_removed_room_disappears_from_the_room_list(
        self, act, test_room, test_player, player_service, connection_manager, outbox
    ):
        browsing = await player_service.create_player(username="Browsing")
        connection_manager.player_sockets = {test_player.id: object(), browsing.id: object()}

        await act(test_player, "leave_room")

        rooms_lists = [
            m["payload"] for player_id, m in outbox if player_id == browsing.id and m["event"] == "rooms_list"
        ]
        assert rooms_lists[-1] == []


class TestJoinRacingLastLeave:
    async def test_newcomer_never_ends_up_in_a_removed_room(
        self, act, test_room, test_player, player_service, room_service
    ):
        newcomer = await player_service.create_player(username="Newcomer")

        leave_reply, join_reply = await asyncio.gather(
            act(test_player, "leave_room"),
            act(newcomer, "join_room", {"room_id": test_room.id}),
        )

        assert leave_reply["event"] == "ack"
        if join_reply["event"] == "ack":
            # joined before the owner left: the room lives on with the newcomer as its owner
            assert await room_service.rooms.get(test_room.id) is test_room
            assert test_room.players == [newcomer]
        else:
            assert join_reply["payload"]["code"] == "room_not_found"
            assert newcomer.room_id is None
