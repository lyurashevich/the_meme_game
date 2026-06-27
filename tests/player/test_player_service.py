from unittest.mock import Mock

import pytest

from app.game.enums import WebsocketEvents
from app.schemas.players import PlayerProfileUpdateSchema
from app.services.player_service import PlayerService


@pytest.fixture
def game_manager():
    m = Mock()
    m.players = {}
    m.get_room = Mock()
    return m


@pytest.fixture
def sender():
    return Mock()


@pytest.fixture
def connection_manager():
    return Mock()


@pytest.fixture
def player_service(game_manager, sender, connection_manager):
    return PlayerService(game_manager, sender, connection_manager)


class TestPlayerService:

    def test_update_player_profile__no_room(self, test_player, player_service, sender, connection_manager):
        new_username = "new"
        test_player.room_id = None

        player_service.manager.players[test_player.id] = test_player

        player_service.update_player_profile(test_player.id, PlayerProfileUpdateSchema(username=new_username))

        assert test_player.username == new_username

        sender.send.assert_called_once_with(
            test_player.id, WebsocketEvents.PLAYER_PROFILE_UPDATED.value, {"username": new_username}
        )
        connection_manager.broadcast_to_room.assert_not_called()

    def test_update_player_profile__in_room(
        self, test_player, connection_manager, game_manager, sender, player_service, test_room
    ):
        new_username = "new"
        test_player.room_id = test_room.id
        game_manager.get_room.return_value = test_room
        test_room.players = [test_player]

        player_service.manager.players[test_player.id] = test_player

        player_service.update_player_profile(test_player.id, PlayerProfileUpdateSchema(username=new_username))

        assert test_player.username == new_username

        sender.send.assert_not_called()
        connection_manager.broadcast_to_room.assert_called_once_with(
            [player.id for player in test_room.players],
            {"event": WebsocketEvents.PLAYER_PROFILE_UPDATED, "username": new_username, "player_id": test_player.id},
        )
