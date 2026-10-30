import json
from unittest.mock import AsyncMock

import pytest

from app.game.dataclasses import Player
from app.game.enums import GameState, RoundState, WebsocketEvents
from app.models import MemeCard, SituationCard
from app.websockets.dispatcher import ActionContext
from app.websockets.handlers import dispatcher


@pytest.fixture
def act(services, session_factory):
    """Send an action as ``player`` through the real dispatcher and handlers; returns the reply."""

    async def act(player, event, payload=None):
        ctx = ActionContext(player=player, services=services, session_factory=session_factory)
        raw = json.dumps({"event": event, "request_id": "r1", "payload": payload or {}})
        return await dispatcher.dispatch(ctx, raw)

    return act


@pytest.fixture
def broadcasts(connection_manager):
    connection_manager.broadcast_to_players = AsyncMock()
    return connection_manager.broadcast_to_players


def sent_events(broadcasts):
    return [call.args[1]["event"] for call in broadcasts.await_args_list]


def error_code(reply):
    assert reply["event"] == "error", reply
    return reply["payload"]["code"]


@pytest.fixture
async def lone_player(player_service):
    return await player_service.create_player(username="Loner")


@pytest.fixture
async def started_game(prepared_game, game_service):
    await game_service.start_first_round(prepared_game.room_id)
    yield prepared_game
    game_service.game_manager.clear_room_tasks(prepared_game.room_id)


class TestUpdateProfile:
    async def test_updates_username_and_avatar(self, act, test_player):
        reply = await act(test_player, "update_profile", {"username": "  Neo  ", "avatar_id": "cat"})

        assert reply["event"] == "ack"
        assert reply["payload"] == {"username": "Neo", "avatar_id": "cat"}
        assert test_player.username == "Neo"
        assert test_player.avatar_id == "cat"

    async def test_empty_payload_changes_nothing(self, act, test_player):
        reply = await act(test_player, "update_profile")

        assert reply["event"] == "ack"
        assert test_player.username == "Lisaveta"

    @pytest.mark.parametrize("username", ["", "   ", "x" * 33])
    async def test_invalid_username(self, act, test_player, username):
        reply = await act(test_player, "update_profile", {"username": username})

        assert error_code(reply) == "validation_error"
        assert test_player.username == "Lisaveta"


class TestCreateRoom:
    async def test_creates_room_owned_by_sender(self, act, test_player, room_service):
        reply = await act(test_player, "create_room", {"name": "Memes", "max_players": 5})

        room = await room_service.get_room(reply["payload"]["room_id"])
        assert room.name == "Memes"
        assert room.max_players == 5
        assert room.owner is test_player
        assert test_player.room_id == room.id

    async def test_announces_room_to_players_outside_rooms(
        self, act, test_player, test_room, lone_player, connection_manager, broadcasts
    ):
        connection_manager.player_sockets = {test_player.id: object(), lone_player.id: object()}

        await act(lone_player, "create_room")

        recipients, message = broadcasts.await_args.args
        assert message["event"] == WebsocketEvents.ROOM_CREATED.value
        # test_player is busy in test_room; lone_player is now in the new room
        assert recipients == []

    async def test_player_already_in_a_room(self, act, test_player, test_room):
        reply = await act(test_player, "create_room")

        assert error_code(reply) == "already_in_a_room"

    @pytest.mark.parametrize("max_players", [2, 11])
    async def test_invalid_max_players(self, act, lone_player, max_players):
        reply = await act(lone_player, "create_room", {"max_players": max_players})

        assert error_code(reply) == "validation_error"
        assert lone_player.room_id is None


class TestJoinRoom:
    async def test_joins_room_and_notifies_players(self, act, test_room, lone_player, broadcasts):
        reply = await act(lone_player, "join_room", {"room_id": test_room.id})

        assert reply["payload"] == {"room_id": test_room.id}
        assert lone_player in test_room.players
        assert lone_player.room_id == test_room.id
        assert sent_events(broadcasts) == [
            WebsocketEvents.YOU_JOINED_THE_ROOM.value,
            WebsocketEvents.PLAYER_JOINED_ROOM.value,
        ]

    async def test_player_already_in_a_room(self, act, test_player, test_room, room_service):
        other_room = await room_service.create_room(owner=Player(username="Other"))

        reply = await act(test_player, "join_room", {"room_id": other_room.id})

        assert error_code(reply) == "already_in_a_room"
        assert test_player not in other_room.players

    async def test_room_not_found(self, act, lone_player):
        reply = await act(lone_player, "join_room", {"room_id": "nope"})

        assert error_code(reply) == "room_not_found"


class TestLeaveRoom:
    async def test_leaves_room(self, act, test_room, lone_player, room_service):
        await room_service.join_room(test_room.id, lone_player)

        reply = await act(lone_player, "leave_room")

        assert reply["payload"] == {"requires_confirmation": False}
        assert lone_player not in test_room.players
        assert lone_player.room_id is None

    async def test_leaving_mid_game_below_minimum_asks_for_confirmation(self, act, started_game):
        # 4 players: the first one can leave freely, the next leave would drop the room below 3
        assert (await act(started_game.room.players[3], "leave_room"))["payload"] == {"requires_confirmation": False}
        leaver = started_game.room.players[1]

        reply = await act(leaver, "leave_room")

        assert reply["payload"] == {"requires_confirmation": True}
        assert leaver in started_game.room.players

    async def test_not_in_a_room(self, act, lone_player):
        reply = await act(lone_player, "leave_room")

        assert error_code(reply) == "player_not_in_room"


class TestUpdateSettings:
    async def test_owner_updates_settings(self, act, test_player, test_room):
        reply = await act(test_player, "update_settings", {"round_time_limit": 90, "max_rounds": 5})

        assert reply["payload"] == {"round_time_limit": 90, "max_rounds": 5, "score_to_win": None}
        assert test_room.settings.round_time_limit == 90
        assert test_room.settings.max_rounds == 5

    async def test_not_owner(self, act, test_room, lone_player, room_service):
        await room_service.join_room(test_room.id, lone_player)

        reply = await act(lone_player, "update_settings", {"round_time_limit": 90})

        assert error_code(reply) == "not_room_owner_exception"
        assert test_room.settings.round_time_limit == 60

    @pytest.mark.parametrize(
        "settings",
        [{"round_time_limit": 61}, {"round_time_limit": 60, "max_rounds": 0}, {"max_rounds": 5}],
    )
    async def test_invalid_settings(self, act, test_player, test_room, settings):
        reply = await act(test_player, "update_settings", settings)

        assert error_code(reply) == "validation_error"


class TestStartGame:
    @pytest.fixture
    async def cards_in_db(self, db_session):
        db_session.add_all([MemeCard(image_url=f"http://memes.org/{i}") for i in range(30)])
        db_session.add_all([SituationCard(text=f"situation {i}") for i in range(5)])
        await db_session.commit()

    async def test_owner_starts_game(
        self, act, test_player, test_room_with_players, game_manager, cards_in_db, broadcasts
    ):
        reply = await act(test_player, "start_game")

        assert reply["event"] == "ack", reply
        game = await game_manager.get_game(test_room_with_players.id)
        assert game.state == GameState.ACTIVE
        assert game.current_round.leader is test_player
        assert sent_events(broadcasts)[0] == WebsocketEvents.GAME_STARTED.value
        game_manager.clear_room_tasks(test_room_with_players.id)

    async def test_not_owner(self, act, test_room_with_players, game_manager, cards_in_db):
        reply = await act(test_room_with_players.players[1], "start_game")

        assert error_code(reply) == "not_room_owner_exception"
        assert await game_manager.games.get(test_room_with_players.id) is None

    async def test_not_enough_players(self, act, test_player, test_room, cards_in_db):
        reply = await act(test_player, "start_game")

        assert error_code(reply) == "not_enough_players"


class TestEndGame:
    async def test_owner_ends_game(self, act, test_player, started_game):
        reply = await act(test_player, "end_game")

        assert reply["event"] == "ack"
        assert started_game.state == GameState.FINISHED

    async def test_not_owner(self, act, started_game):
        reply = await act(started_game.room.players[1], "end_game")

        assert error_code(reply) == "not_room_owner_exception"
        assert started_game.state == GameState.ACTIVE


class TestSelectCard:
    async def test_player_selects_card(self, act, started_game):
        player = started_game.room.players[1]
        card = player.hand_cards[0]

        reply = await act(player, "select_card", {"card_id": card.id})

        assert reply["event"] == "ack"
        assert started_game.current_round.player_choices[player.id] is card
        assert card not in player.hand_cards

    async def test_leader_cannot_select(self, act, test_player, started_game):
        reply = await act(test_player, "select_card", {"card_id": test_player.hand_cards[0].id})

        assert error_code(reply) == "invalid_player_action"


class TestChooseWinner:
    @pytest.fixture
    async def judging_round(self, started_game, game_service):
        for player in started_game.room.players[1:]:
            await game_service.player_select_card(started_game.room_id, player.id, player.hand_cards[0].id)
        assert started_game.current_round.state == RoundState.LEADER_CHOOSING
        return started_game

    async def test_leader_chooses_winner(self, act, test_player, judging_round):
        winner = judging_round.room.players[2]
        card_id = judging_round.current_round.player_choices[winner.id].id

        reply = await act(test_player, "choose_winner", {"card_id": card_id})

        assert reply["event"] == "ack"
        assert winner.score == 1

    async def test_not_leader(self, act, judging_round):
        player = judging_round.room.players[2]
        card_id = judging_round.current_round.player_choices[player.id].id

        reply = await act(player, "choose_winner", {"card_id": card_id})

        assert error_code(reply) == "not_round_leader"
        assert player.score == 0
