"""At most CHAT_RATE_LIMIT chat messages per CHAT_RATE_WINDOW_SECONDS per connection.

Before: a player could send messages as fast as the socket allowed - each one broadcast to
the whole room, pushing the 50-message history out in a blink.
"""

import json

import pytest

from app.websockets.dispatcher import (
    CHAT_RATE_LIMIT,
    CHAT_RATE_WINDOW_SECONDS,
    ActionContext,
)
from app.websockets.handlers import dispatcher
from app.websockets.rate_limiter import RateLimiter
from tests.helpers import WsClient, events_for


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class TestRateLimiter:
    def test_allows_up_to_the_limit_within_the_window(self):
        clock = FakeClock()
        limiter = RateLimiter(limit=3, window_seconds=10, clock=clock)

        assert [limiter.try_acquire() for _ in range(3)] == [None, None, None]
        assert limiter.try_acquire() == 10  # the oldest action leaves the window in 10 s

    def test_window_slides(self):
        clock = FakeClock()
        limiter = RateLimiter(limit=2, window_seconds=10, clock=clock)
        limiter.try_acquire()  # t=0
        clock.now += 4
        limiter.try_acquire()  # t=4

        clock.now += 5  # t=9: both still within the last 10 s
        assert limiter.try_acquire() == pytest.approx(1)

        clock.now += 1  # t=10: the first one has left the window
        assert limiter.try_acquire() is None
        assert limiter.try_acquire() == pytest.approx(4)  # t=4 and t=10 are in it now

    def test_rejected_attempts_are_not_counted(self):
        clock = FakeClock()
        limiter = RateLimiter(limit=1, window_seconds=10, clock=clock)
        limiter.try_acquire()

        for _ in range(100):  # someone hammering "send"
            clock.now += 0.05
            assert limiter.try_acquire() is not None

        clock.now = 1010  # 10 s after the only accepted message
        assert limiter.try_acquire() is None


@pytest.fixture
def connection(services, session_factory):
    """One player's connection: the same context - and so the same rate limiter - for every message."""

    def connection(player, clock=None):
        limiter = RateLimiter(CHAT_RATE_LIMIT, CHAT_RATE_WINDOW_SECONDS, clock=clock) if clock else None
        ctx = ActionContext(player=player, services=services, session_factory=session_factory)
        if limiter:
            ctx.chat_rate_limiter = limiter

        async def say(text):
            raw = json.dumps({"event": "chat_message", "request_id": "r", "payload": {"text": text}})
            return await dispatcher.dispatch(ctx, raw)

        return say

    return connection


class TestChatRateLimit:
    async def test_too_many_messages_are_rejected_and_not_sent(self, test_room_with_players, connection, outbox):
        player = test_room_with_players.players[1]
        say = connection(player)

        replies = [await say(f"message {i}") for i in range(CHAT_RATE_LIMIT + 1)]

        assert [reply["event"] for reply in replies] == ["ack"] * CHAT_RATE_LIMIT + ["error"]
        assert replies[-1]["payload"]["code"] == "too_many_messages"
        assert "Try again in 10 s" in replies[-1]["payload"]["message"]
        assert len(test_room_with_players.messages) == CHAT_RATE_LIMIT
        for other in test_room_with_players.players:
            chats = [m for m in events_for(outbox, other.id) if m["event"] == "chat_message"]
            assert len(chats) == CHAT_RATE_LIMIT

    async def test_the_limit_is_per_player(self, test_room_with_players, connection):
        spammer, other = test_room_with_players.players[1], test_room_with_players.players[2]
        say_spam = connection(spammer)
        for i in range(CHAT_RATE_LIMIT + 1):
            await say_spam(f"spam {i}")

        assert (await connection(other)("hi"))["event"] == "ack"

    async def test_allowed_again_once_the_window_has_passed(self, test_room_with_players, connection):
        clock = FakeClock()
        say = connection(test_room_with_players.players[1], clock=clock)
        for i in range(CHAT_RATE_LIMIT):
            await say(f"message {i}")
        assert (await say("one too many"))["event"] == "error"

        clock.now += CHAT_RATE_WINDOW_SECONDS

        assert (await say("back again"))["event"] == "ack"

    async def test_invalid_messages_dont_count(self, test_room_with_players, connection):
        say = connection(test_room_with_players.players[1])
        for _ in range(CHAT_RATE_LIMIT * 2):
            assert (await say("   "))["payload"]["code"] == "validation_error"

        assert (await say("still allowed"))["event"] == "ack"


class TestOverWebsocket:
    def test_spamming_gets_an_error_and_the_connection_survives(self, client_with_no_db):
        with client_with_no_db.websocket_connect("/ws") as ws:
            client = WsClient(ws)
            client.act("create_room")

            replies = [client.send("chat_message", {"text": f"message {i}"}) for i in range(CHAT_RATE_LIMIT + 1)]

            assert replies[-1]["payload"]["code"] == "too_many_messages"
            assert client.send("update_profile", {"username": "Calm"})["event"] == "ack"  # still connected
