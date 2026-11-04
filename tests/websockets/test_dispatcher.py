import json

import pytest

from app.exceptions import NotRoomOwnerException
from app.game.dataclasses import Player
from app.websockets.dispatcher import ActionContext, Dispatcher
from app.websockets.protocol import ActionPayload
from tests.helpers import WsClient


class EchoPayload(ActionPayload):
    value: int


@pytest.fixture
def dispatcher():
    dispatcher = Dispatcher()

    @dispatcher.action("echo", EchoPayload)
    async def echo(ctx, payload):
        return {"value": payload.value, "player_id": ctx.player.id}

    @dispatcher.action("no_result")
    async def no_result(ctx, payload):
        return None

    @dispatcher.action("forbidden")
    async def forbidden(ctx, payload):
        raise NotRoomOwnerException()

    @dispatcher.action("crash")
    async def crash(ctx, payload):
        raise RuntimeError("boom")

    return dispatcher


@pytest.fixture
def ctx(services):
    return ActionContext(player=Player(id="p1", username="Lisaveta"), services=services, session_factory=None)


def message(event, payload=None, request_id="req-1"):
    return json.dumps({"event": event, "request_id": request_id, "payload": payload or {}})


class TestDispatcher:
    async def test_ack_with_handler_result_and_player_from_context(self, dispatcher, ctx):
        reply = await dispatcher.dispatch(ctx, message("echo", {"value": 5}))

        assert reply == {"event": "ack", "request_id": "req-1", "payload": {"value": 5, "player_id": "p1"}}

    async def test_ack_with_empty_payload_when_handler_returns_none(self, dispatcher, ctx):
        reply = await dispatcher.dispatch(ctx, message("no_result"))

        assert reply == {"event": "ack", "request_id": "req-1", "payload": {}}

    async def test_request_id_is_optional(self, dispatcher, ctx):
        reply = await dispatcher.dispatch(ctx, json.dumps({"event": "no_result"}))

        assert reply["event"] == "ack"
        assert reply["request_id"] is None

    @pytest.mark.parametrize("raw", ["not json", "[]", "{}", '{"event": 1}'])
    async def test_invalid_message(self, dispatcher, ctx, raw):
        reply = await dispatcher.dispatch(ctx, raw)

        assert reply["event"] == "error"
        assert reply["request_id"] is None
        assert reply["payload"]["code"] == "invalid_message"
        json.dumps(reply)  # details must be serializable to be sent over the socket

    async def test_unknown_event(self, dispatcher, ctx):
        reply = await dispatcher.dispatch(ctx, message("nope"))

        assert reply["request_id"] == "req-1"
        assert reply["payload"]["code"] == "unknown_event"

    @pytest.mark.parametrize("payload", [{}, {"value": "abc"}, {"value": 1, "player_id": "someone_else"}])
    async def test_invalid_payload(self, dispatcher, ctx, payload):
        reply = await dispatcher.dispatch(ctx, message("echo", payload))

        assert reply["event"] == "error"
        assert reply["request_id"] == "req-1"
        assert reply["payload"]["code"] == "validation_error"
        assert reply["payload"]["details"]
        json.dumps(reply)

    async def test_custom_exception_becomes_error_with_its_code(self, dispatcher, ctx):
        reply = await dispatcher.dispatch(ctx, message("forbidden"))

        assert reply == {
            "event": "error",
            "request_id": "req-1",
            "payload": {"code": NotRoomOwnerException.code, "message": NotRoomOwnerException.message},
        }

    async def test_unexpected_exception_is_logged_and_hidden(self, dispatcher, ctx, caplog):
        reply = await dispatcher.dispatch(ctx, message("crash"))

        assert reply["payload"] == {"code": "internal_error", "message": "Internal server error"}
        assert "boom" not in json.dumps(reply)
        assert "crash" in caplog.text

    def test_duplicate_registration_is_rejected(self, dispatcher):
        with pytest.raises(ValueError):

            @dispatcher.action("echo")
            async def another_echo(ctx, payload):
                return None


class TestChatMessageAction:
    """End-to-end through the real websocket endpoint and the registered handlers."""

    def test_chat_message_is_broadcast_to_the_room(self, client_with_no_db):
        with (
            client_with_no_db.websocket_connect("/ws") as alice_ws,
            client_with_no_db.websocket_connect("/ws") as bob_ws,
        ):
            alice, bob = WsClient(alice_ws), WsClient(bob_ws)
            room_id = alice.act("create_room")["room_id"]
            bob.act("join_room", {"room_id": room_id})

            assert alice.send("chat_message", {"text": "  hi  "}) == {
                "event": "ack",
                "request_id": "chat_message",
                "payload": {},
            }

            for client in (alice, bob):
                chat = client.next("chat_message")["payload"]
                assert chat["player_id"] == alice.player_id
                assert chat["text"] == "hi"
                assert set(chat) == {"player_id", "username", "text", "timestamp"}

            # someone joining later gets the history in their first snapshot
            with client_with_no_db.websocket_connect("/ws") as carol_ws:
                carol = WsClient(carol_ws)
                carol.act("join_room", {"room_id": room_id})
                assert [m["text"] for m in carol.next("room_state")["payload"]["chat"]] == ["hi"]

    def test_chat_message_outside_room_is_rejected(self, client_with_no_db):
        with client_with_no_db.websocket_connect("/ws") as ws:
            reply = WsClient(ws).send("chat_message", {"text": "hi"})

        assert reply["event"] == "error"
        assert reply["payload"]["code"] == "player_not_in_room"

    @pytest.mark.parametrize("text", ["", "   ", "x" * 501])
    def test_chat_message_text_is_validated(self, client_with_no_db, text):
        with client_with_no_db.websocket_connect("/ws") as ws:
            reply = WsClient(ws).send("chat_message", {"text": text})

        assert reply["payload"]["code"] == "validation_error"

    def test_connection_survives_errors(self, client_with_no_db):
        with client_with_no_db.websocket_connect("/ws") as ws:
            client = WsClient(ws)
            client.next("rooms_list")
            ws.send_text("garbage")
            assert ws.receive_json()["payload"]["code"] == "invalid_message"

            ws.send_json({"event": "unknown", "request_id": "r2"})
            assert ws.receive_json()["payload"]["code"] == "unknown_event"
