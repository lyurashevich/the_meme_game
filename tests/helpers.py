"""Test helpers: assertions on messages captured by the ``outbox`` fixture and a websocket test client."""

TEST_ADMIN_TOKEN = "test-admin-token"  # what the admin_headers fixture configures and sends


def events_for(outbox, player_id):
    return [message for recipient, message in outbox if recipient == player_id]


def last_room_state(outbox, player_id):
    """The latest ``room_state`` payload ``player_id`` received - i.e. what their screen shows."""
    states = [m["payload"] for m in events_for(outbox, player_id) if m["event"] == "room_state"]
    assert states, f"{player_id} received no room_state"
    return states[-1]


class WsClient:
    """Wraps a TestClient websocket. Keeps every message it hasn't consumed yet, since
    broadcasts and replies to our own requests interleave, so tests can ask for
    "the next room_state" or "the reply to my request" regardless of what came in between."""

    def __init__(self, ws):
        self.ws = ws
        self.inbox = []
        self.player_id = self.next("session")["payload"]["player_id"]

    def next(self, event, where=None):
        """Return (and consume) the first message of type ``event`` (matching ``where``), waiting if needed."""

        def matches(message):
            return message["event"] == event and (where is None or where(message["payload"]))

        for message in self.inbox:
            if matches(message):
                self.inbox.remove(message)
                return message

        while True:
            message = self.ws.receive_json()
            if matches(message):
                return message
            self.inbox.append(message)

    def send(self, event, payload=None):
        """Send an action and return the ack/error reply to it."""
        self.ws.send_json({"event": event, "request_id": event, "payload": payload or {}})
        while True:
            message = self.ws.receive_json()
            if message["event"] in ("ack", "error") and message["request_id"] == event:
                return message
            self.inbox.append(message)

    def act(self, event, payload=None):
        """Send an action that must succeed; return the ack payload."""
        reply = self.send(event, payload)
        assert reply["event"] == "ack", reply
        return reply["payload"]
