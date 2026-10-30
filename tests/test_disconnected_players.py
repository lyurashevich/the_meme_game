"""A player who disconnects has reconnect_timeout seconds to come back; after that they leave
their room the regular way and are forgotten.

Before: nothing was ever scheduled. A disconnected player stayed in their room forever (every
round then waited for their card until the timer ran out), a room whose players all closed the
tab kept playing rounds on its own, and every player who ever opened the page stayed in memory.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.exceptions import InvalidReconnectToken
from app.game.enums import GameEndReason, GameState
from app.websockets.views import websocket_endpoint
from tests.helpers import WsClient, events_for, last_room_state


@pytest.fixture
def reconnect_service(reconnect_service):
    reconnect_service.reconnect_timeout = 0
    return reconnect_service


def _now():
    return datetime.now(timezone.utc)


async def disconnect_and_wait(reconnect_service, player):
    """The player's socket closes and they never come back."""
    await reconnect_service.disconnect(player.id)
    await reconnect_service._removal_tasks[player.id]


async def assert_forgotten(player, player_service, reconnect_service):
    assert await player_service.players.get(player.id) is None
    assert await reconnect_service.tokens.get_token_for_player(player.id) is None
    assert player.id not in reconnect_service._removal_tasks


class TestNotBackInTime:
    async def test_player_outside_rooms_is_forgotten(self, player_service, reconnect_service):
        visitor = await player_service.create_player(username="JustLooked")
        await reconnect_service.create_reconnect_token(visitor.id)

        await disconnect_and_wait(reconnect_service, visitor)

        await assert_forgotten(visitor, player_service, reconnect_service)

    async def test_player_leaves_their_room(self, test_room_with_players, player_service, reconnect_service, outbox):
        gone = test_room_with_players.players[2]

        await disconnect_and_wait(reconnect_service, gone)

        assert gone not in test_room_with_players.players
        await assert_forgotten(gone, player_service, reconnect_service)
        for player in test_room_with_players.players:
            assert gone.id not in {p["id"] for p in last_room_state(outbox, player.id)["players"]}

    async def test_leader_leaving_mid_game_starts_a_new_round(
        self, prepared_game, game_service, player_service, reconnect_service
    ):
        await game_service.start_first_round(prepared_game.room_id)
        leader = prepared_game.current_round.leader

        await disconnect_and_wait(reconnect_service, leader)

        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.round_number == 2
        assert prepared_game.current_round.leader is not leader
        await assert_forgotten(leader, player_service, reconnect_service)
        game_service.game_manager.clear_room_tasks(prepared_game.room_id)

    async def test_game_ends_when_too_few_players_remain(self, prepared_game, game_service, reconnect_service, outbox):
        await game_service.start_first_round(prepared_game.room_id)
        first, second = prepared_game.room.players[2], prepared_game.room.players[3]

        await disconnect_and_wait(reconnect_service, first)  # 4 -> 3: the game goes on
        assert prepared_game.state == GameState.ACTIVE
        await disconnect_and_wait(reconnect_service, second)  # 3 -> 2: too few

        assert prepared_game.state == GameState.FINISHED
        owner = prepared_game.room.owner
        endings = [m["payload"]["reason"] for m in events_for(outbox, owner.id) if m["event"] == "game_ended"]
        assert endings == [GameEndReason.NOT_ENOUGH_PLAYERS.value]

    async def test_room_of_players_who_all_left_is_removed(
        self, prepared_game, game_service, reconnect_service, room_service, game_manager
    ):
        await game_service.start_first_round(prepared_game.room_id)

        for player in list(prepared_game.room.players):
            await disconnect_and_wait(reconnect_service, player)

        assert await room_service.rooms.get(prepared_game.room_id) is None
        assert await game_manager.games.get(prepared_game.room_id) is None
        assert prepared_game.room_id not in game_manager.room_tasks  # no rounds playing on their own


class TestBackInTime:
    async def test_reconnecting_cancels_the_removal(self, test_room, test_player, player_service, reconnect_service):
        reconnect_service.reconnect_timeout = 60
        token = await reconnect_service.create_reconnect_token(test_player.id)
        await reconnect_service.disconnect(test_player.id)
        removal = reconnect_service._removal_tasks[test_player.id]

        player = await reconnect_service.handle_reconnect(token, _now())
        await asyncio.sleep(0)

        assert player is test_player
        assert removal.cancelled()
        assert test_player.is_connected
        assert test_player in test_room.players
        assert await player_service.players.get(test_player.id) is test_player

    async def test_removal_that_already_started_wins(self, test_player, reconnect_service):
        reconnect_service.reconnect_timeout = 60  # the token is still valid: only the removal can stop it
        token = await reconnect_service.create_reconnect_token(test_player.id)
        await reconnect_service.disconnect(test_player.id)

        await reconnect_service.remove_player(test_player.id)  # the timer fired first

        with pytest.raises(InvalidReconnectToken):
            await reconnect_service.handle_reconnect(token, _now())

    async def test_removal_does_nothing_if_the_player_is_back(self, test_room, test_player, reconnect_service):
        reconnect_service.reconnect_timeout = 60  # the token is still valid: only the removal can stop it
        token = await reconnect_service.create_reconnect_token(test_player.id)
        await reconnect_service.disconnect(test_player.id)
        await reconnect_service.handle_reconnect(token, _now())

        await reconnect_service.remove_player(test_player.id)  # a removal that got here late

        assert test_player in test_room.players


class TestStaleSocket:
    """A phone switching from Wi-Fi to mobile data reconnects on a new socket before the server
    notices the old one is dead. When the old one finally closes, nothing must happen."""

    def test_connection_manager_only_forgets_the_current_socket(self, connection_manager):
        old, new = object(), object()
        connection_manager.add_connection("p1", new)

        assert connection_manager.remove_connection("p1", old) is False
        assert connection_manager.get_connection("p1") is new
        assert connection_manager.remove_connection("p1", new) is True
        assert connection_manager.get_connection("p1") is None

    async def test_old_socket_closing_after_a_reconnect_changes_nothing(
        self, websocket, services, player_service, connection_manager, reconnect_service, test_player
    ):
        new_socket = object()

        async def reconnect_elsewhere_then_drop():
            connection_manager.add_connection(test_player.id, new_socket)  # the new connection arrives
            raise WebSocketDisconnect()  # ...and only then does the old one die

        websocket.receive_text = AsyncMock(side_effect=reconnect_elsewhere_then_drop)
        with patch.object(player_service, "create_player", new_callable=AsyncMock, return_value=test_player):
            await websocket_endpoint(websocket=websocket, reconnect_token=None, services=services)

        assert connection_manager.get_connection(test_player.id) is new_socket
        assert test_player.is_connected
        assert test_player.id not in reconnect_service._removal_tasks


class TestOverWebsockets:
    def test_others_see_the_player_go_offline_then_leave(self, client_with_no_db, reconnect_service):
        reconnect_service.reconnect_timeout = 0.05

        with client_with_no_db.websocket_connect("/ws") as owner_ws:
            owner = WsClient(owner_ws)
            room_id = owner.act("create_room")["room_id"]

            with client_with_no_db.websocket_connect("/ws") as guest_ws:
                guest = WsClient(guest_ws)
                guest.act("join_room", {"room_id": room_id})
                owner.next("room_state", lambda s: len(s["players"]) == 2)

            offline = owner.next("room_state", lambda s: any(not p["is_connected"] for p in s["players"]))
            assert {p["id"]: p["is_connected"] for p in offline["payload"]["players"]}[guest.player_id] is False

            # later than the "offline" snapshot - the one from creating the room also had a single player
            went_offline_at = offline["payload"]["server_time"]
            gone = owner.next("room_state", lambda s: len(s["players"]) == 1 and s["server_time"] > went_offline_at)
            assert [p["id"] for p in gone["payload"]["players"]] == [owner.player_id]
