"""A whole round played by three players over real websocket connections."""

from contextlib import ExitStack
from datetime import datetime, timedelta

from app.models import MemeCard, SituationCard
from tests.helpers import WsClient


def in_round(number, round_state=None):
    """Matcher for ``WsClient.next``: a room_state showing the given round (and phase)."""

    def matches(state):
        game = state["game"]
        return (
            game is not None
            and game["round_number"] == number
            and (round_state is None or game["round_state"] == round_state)
        )

    return matches


async def test_full_round_over_websockets(client_with_no_db, db_session, game_service):
    db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(30)])
    db_session.add_all([SituationCard(text=f"situation {i}") for i in range(5)])
    await db_session.commit()
    game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0.05

    with ExitStack() as stack:
        owner, second, third = (
            WsClient(stack.enter_context(client_with_no_db.websocket_connect("/ws"))) for _ in range(3)
        )
        players = (owner, second, third)

        room_id = owner.act("create_room")["room_id"]
        second.act("join_room", {"room_id": room_id})
        third.act("join_room", {"room_id": room_id})

        owner.act("start_game")
        screens = {client: client.next("room_state", in_round(1))["payload"]["game"] for client in players}
        assert screens[owner]["leader_id"] == owner.player_id
        assert screens[owner]["round_state"] == "choosing_cards"
        assert screens[owner]["ends_at"]  # the countdown for the choosing phase

        # the leader can't play a card, the others can
        assert owner.send("select_card", {"card_id": 1})["payload"]["code"] == "invalid_player_action"

        chosen = {}
        for client in (second, third):
            card_id = screens[client]["my_hand"][0]["id"]
            client.act("select_card", {"card_id": card_id})
            chosen[client] = card_id

        # everyone played: the leader judges an anonymous table
        judging_state = owner.next("room_state", in_round(1, "leader_choosing"))["payload"]
        judging = judging_state["game"]
        assert sorted(card["id"] for card in judging["table"]) == sorted(chosen.values())
        # the leader gets their own countdown, computed the way the client does it
        remaining = datetime.fromisoformat(judging["ends_at"]) - datetime.fromisoformat(judging_state["server_time"])
        assert timedelta(seconds=28) < remaining <= timedelta(seconds=game_service.LEADER_TIME_LIMIT_SECONDS)

        # only the leader picks the winner; the ack comes back before the next round starts
        assert second.send("choose_winner", {"card_id": chosen[third]})["payload"]["code"] == "not_round_leader"
        owner.act("choose_winner", {"card_id": chosen[third]})

        for client in players:
            assert client.next("round_winner")["payload"] == {"winner_id": third.player_id, "card_id": chosen[third]}

            next_round = client.next("room_state", in_round(2))["payload"]
            assert next_round["game"]["leader_id"] == second.player_id
            scores = {p["id"]: p["score"] for p in next_round["players"]}
            assert scores[third.player_id] == 1

        owner.act("end_game")
        game_ended = second.next("game_ended")["payload"]
        assert game_ended["reason"] == "owner_ended"
        assert game_ended["winner_ids"] == [third.player_id]
        assert second.next("room_state", lambda state: state["game"] is None)
