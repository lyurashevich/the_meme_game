import pytest

from app.exceptions import (
    AlreadyInARoomException,
    PlayerNotInRoomException,
    RoomIsFullException,
)
from app.game.dataclasses import Game, Player, Room
from app.game.enums import GameState


class TestPlayer:
    async def test_create_player(self):
        player = Player(id="1", username="Lisaveta")
        assert player.id == "1"
        assert player.username == "Lisaveta"
        assert player.hand_cards == []
        assert not player.is_host
        assert player.score == 0
        assert player.is_connected
        assert player.connection_order == 0

    async def test_update_player(self, test_player):
        old_username = test_player.username
        test_player.username = "Oleg"

        assert old_username != test_player.username


class TestRoom:
    async def test_create_room(self, test_player):
        room = Room(owner=test_player)
        assert isinstance(room.id, str)
        assert room.max_players == 10
        assert room.owner == test_player
        assert not room.is_private
        assert len(room.players) == 1
        assert test_player in room.players

    async def test_add_player(self, test_room):
        player = Player(id="2", username="Lisaveta")

        players_quantity = len(test_room.players)

        test_room.add_player(player)

        assert players_quantity != len(test_room.players)
        assert len(test_room.players) == 2
        assert test_room.owner in test_room.players
        assert player in test_room.players

    async def test_add_player__already_joined(self, test_room):
        player = Player(id="2", username="Lisaveta")
        test_room.add_player(player)

        with pytest.raises(AlreadyInARoomException):
            test_room.add_player(player)

    async def test_add_player__room_is_full(self, test_room):
        test_room.max_players = 1
        player = Player(id="2", username="Lisaveta")

        with pytest.raises(RoomIsFullException):
            test_room.add_player(player)

    async def test_remove_player__not_found(self, test_room):
        player = Player(id="2", username="Lisaveta")

        with pytest.raises(PlayerNotInRoomException) as e:
            test_room.remove_player(player)

        assert str(e.value.message) == PlayerNotInRoomException.message

    async def test_remove_player(self, test_room):
        player = Player(id="2", username="Lisaveta")
        test_room.add_player(player)

        test_room.remove_player(player)

        assert len(test_room.players) == 1
        assert test_room.owner in test_room.players
        assert player not in test_room.players

    async def test_reassign_owner__promotes_next_player_by_join_order(self, test_room):
        old_owner = test_room.owner
        next_player = Player(id="2", username="Lisaveta")
        later_player = Player(id="3", username="Maria")
        test_room.add_player(next_player)
        test_room.add_player(later_player)

        test_room.remove_player(old_owner)
        test_room.reassign_owner()

        assert test_room.owner is next_player
        assert next_player.is_host is True
        assert old_owner.is_host is False
        assert later_player.is_host is False

    async def test_reassign_owner__no_players_left_sets_owner_none(self, test_room):
        owner = test_room.owner
        test_room.remove_player(owner)

        test_room.reassign_owner()

        assert test_room.owner is None


class TestGame:
    def test_game_create(self, test_player):
        room = Room(owner=test_player)
        game = Game(room=room, settings=room.settings)

        assert isinstance(game.id, str)
        assert game.state == GameState.STARTING
        assert not game.current_round
        assert game.meme_deck == []
        assert game.situation_deck == []
        assert game.meme_discard_pile == {}
        assert game.situation_discard_pile == {}
        assert game.leader_index == 0
