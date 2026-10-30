"""A whole round played by three players over real websocket connections."""

from contextlib import ExitStack

from app.models import MemeCard, SituationCard


class Client:
    """A websocket test client that keeps every message it hasn't consumed yet,
    since broadcasts and replies to our own requests interleave."""

    def __init__(self, ws):
        self.ws = ws
        self.inbox = []
        self.player_id = self.next("player_created")["payload"]["player_id"]

    def next(self, event, request_id=None):
        """Return (and consume) the first message matching ``event``/``request_id``, waiting if needed."""

        def matches(message):
            return message["event"] == event and (request_id is None or message.get("request_id") == request_id)

        for message in self.inbox:
            if matches(message):
                self.inbox.remove(message)
                return message

        while True:
            message = self.ws.receive_json()
            if matches(message):
                return message
            self.inbox.append(message)

    def reply(self, request_id):
        while True:
            message = self.ws.receive_json()
            if message["event"] in ("ack", "error") and message["request_id"] == request_id:
                return message
            self.inbox.append(message)

    def send(self, event, payload=None):
        self.ws.send_json({"event": event, "request_id": event, "payload": payload or {}})
        return self.reply(event)

    def act(self, event, payload=None):
        reply = self.send(event, payload)
        assert reply["event"] == "ack", reply
        return reply["payload"]


async def test_full_round_over_websockets(client_with_no_db, db_session, game_service):
    db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(30)])
    db_session.add_all([SituationCard(text=f"situation {i}") for i in range(5)])
    await db_session.commit()
    game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0.05

    with ExitStack() as stack:
        owner, second, third = (
            Client(stack.enter_context(client_with_no_db.websocket_connect("/ws"))) for _ in range(3)
        )
        players = (owner, second, third)

        room_id = owner.act("create_room")["room_id"]
        second.act("join_room", {"room_id": room_id})
        third.act("join_room", {"room_id": room_id})

        owner.act("start_game")
        rounds = {client: client.next("round_started")["payload"] for client in players}
        assert rounds[owner]["leader_id"] == owner.player_id
        assert rounds[owner]["current_round_number"] == 1

        # the leader can't play a card, the others can
        assert owner.send("select_card", {"card_id": 1})["payload"]["code"] == "invalid_player_action"

        chosen = {}
        for client in (second, third):
            card_id = rounds[client]["player_cards"][0]["id"]
            client.act("select_card", {"card_id": card_id})
            chosen[client] = card_id

        # only the leader picks the winner; the ack comes back before the next round starts
        assert second.send("choose_winner", {"card_id": chosen[third]})["payload"]["code"] == "not_round_leader"
        owner.act("choose_winner", {"card_id": chosen[third]})

        for client in players:
            winner = client.next("leader_has_chosen_winner")["payload"]
            assert winner["winner_id"] == third.player_id

            next_round = client.next("round_started")["payload"]
            assert next_round["current_round_number"] == 2
            assert next_round["leader_id"] == second.player_id
            assert next_round["score"][third.player_id] == 1

        owner.act("end_game")
        assert second.next("game_ended")["payload"]["final_scores"][third.player_id] == 1
