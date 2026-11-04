import asyncio

from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from tests.helpers import events_for, last_room_state


class TestNotifier:
    async def test_room_state_is_personal(self, test_room_with_players, notifier, outbox):
        room = test_room_with_players
        room.players[1].hand_cards = []  # no game: hands don't matter, the recipient does

        await notifier.broadcast_room_state(room.id)

        assert [recipient for recipient, _ in outbox] == [p.id for p in room.players]
        assert all(message["event"] == "room_state" for _, message in outbox)
        assert all("chat" not in message["payload"] for _, message in outbox)

    async def test_chat_history_only_for_the_newcomer(self, test_room_with_players, notifier, outbox):
        room = test_room_with_players
        room.messages = [{"text": "hello"}]
        newcomer = room.players[-1]

        await notifier.broadcast_room_state(room.id, with_chat_for=newcomer.id)

        assert last_room_state(outbox, newcomer.id)["chat"] == [{"text": "hello"}]
        assert "chat" not in last_room_state(outbox, room.players[0].id)

    async def test_missing_room_is_a_no_op(self, notifier, outbox):
        await notifier.broadcast_room_state("gone")
        await notifier.broadcast_event("gone", WebsocketEvents.CHAT_MESSAGE, {})

        assert outbox == []

    async def test_rooms_list_goes_only_to_connected_players_outside_rooms(
        self, test_room, test_player, notifier, player_service, connection_manager, outbox
    ):
        browsing = await player_service.create_player(username="Browsing")
        offline = await player_service.create_player(username="Offline")
        connection_manager.player_sockets = {test_player.id: object(), browsing.id: object()}

        await notifier.broadcast_rooms_list()

        assert [recipient for recipient, _ in outbox] == [browsing.id]
        assert offline.id not in {recipient for recipient, _ in outbox}
        _, message = outbox[0]
        assert message["event"] == "rooms_list"
        assert [room["id"] for room in message["payload"]] == [test_room.id]

    async def test_newer_snapshot_never_arrives_before_an_older_one(
        self, test_room_with_players, notifier, connection_manager
    ):
        """Two broadcasts for the same room must not interleave: the second one waits and is built
        from the state at the time it is sent, so each player's last snapshot is the newest."""
        room = test_room_with_players
        received = []

        async def slow_send(player_id, message):
            name = message["payload"]["room"]["name"]
            # the older broadcast is slow (think of a laggy connection), so without ordering
            # the newer one would overtake it and its stale snapshot would arrive last
            await asyncio.sleep(0.01 if name != "renamed" else 0)
            received.append((player_id, name))

        connection_manager.send_personal_json = slow_send

        first = asyncio.create_task(notifier.broadcast_room_state(room.id))
        await asyncio.sleep(0)  # the first broadcast is now in the middle of sending
        room.name = "renamed"
        second = asyncio.create_task(notifier.broadcast_room_state(room.id))
        await asyncio.gather(first, second)

        for player in room.players:
            names = [name for player_id, name in received if player_id == player.id]
            assert names[-1] == "renamed"

    async def test_session(self, notifier, outbox):
        player = Player(username="Neo", avatar_id="cat")

        await notifier.send_session(player, "token-1")

        assert events_for(outbox, player.id) == [
            {
                "event": "session",
                "payload": {
                    "player_id": player.id,
                    "reconnect_token": "token-1",
                    "username": "Neo",
                    "avatar_id": "cat",
                },
            }
        ]
