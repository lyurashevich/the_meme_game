from unittest.mock import patch

import pytest

from app.game.dataclasses import Game, Player, Room
from app.game.enums import GameState
from app.game.game import GameLogic
from app.game.game_manager import game_manager


class TestPlayer:
    async def test_create_player(self):
        player = Player(id=1, username="Lisaveta")
        assert player.id == 1
        assert player.username == "Lisaveta"
        assert player.handed_cards == []
        assert not player.is_host
        assert player.score == 0
        assert player.is_connected
        assert player.connection_order == 0

    async def test_update_player(self, player):
        old_username = player.username
        player.username = "Oleg"

        assert old_username != player.username


class TestRoom:
    async def test_create_room(self, player):
        room = Room(owner=player)
        assert isinstance(room.id, str)
        assert room.name.startswith("room")
        assert room.max_players == 10
        assert room.owner == player
        assert isinstance(room.invitation_link, str)
        assert not room.is_private
        assert len(room.players) == 1
        assert player in room.players

    async def test_add_player(self, room):
        player = Player(id=2)

        players_quantity = len(room.players)

        await room.add_player(player)

        assert players_quantity != len(room.players)
        assert len(room.players) == 2
        assert room.owner in room.players
        assert player in room.players

    async def test_add_player__already_joined(self, room):
        player = Player(id=2)
        await room.add_player(player)

        with pytest.raises(Exception) as e:
            await room.add_player(player)

        assert "already joined" in str(e.value)

    async def test_add_player__room_is_full(self, room):
        room.max_players = 1
        player = Player(id=2)

        with pytest.raises(Exception) as e:
            await room.add_player(player)

        assert "The room is full" in str(e.value)

    async def test_remove_player__not_found(self, room):
        player = Player(id=2)

        with pytest.raises(Exception) as e:
            await room.remove_player(player)

        assert str(e.value) == "User not found"

    async def test_remove_player(self, room):
        player = Player(id=2)
        await room.add_player(player)

        await room.remove_player(player)

        assert len(room.players) == 1
        assert room.owner in room.players
        assert player not in room.players


class TestGame:
    def test_game_create(self, player):
        room = Room(owner=player)
        game = Game(room=room)

        assert isinstance(game.id, str)
        assert game.state == GameState.WAITING
        assert not game.current_round
        assert game.round_number == 0
        assert game.meme_deck == []
        assert game.situation_deck == []
        assert game.meme_discard_pile == {}
        assert game.situation_discard_pile == {}
        assert game.leader_index == 0

    # def test_start_game__not_enough_players(self, game):
    #     with pytest.raises(Exception) as e:
    #         game.start_game()
    #
    #     assert str(e.value) == "You need to have at least 3 players to start game."
    #
    # def test_start_game(self, game, room, people, mock_meme_cards, mock_situation_cards):
    #     for person in people:
    #         game.room.add_player(person)
    #
    #     game.start_game()
    #
    #     assert game.state == GameState.STARTING
    #     assert game.current_round is not None
    #     assert game.current_round.leader == room.players[0]
    #     assert game.meme_deck != []
    #     assert game.situation_deck != []
    #     assert game.meme_discard_pile == []
    #     assert game.situation_discard_pile == []


class TestGameLogic:
    logic = GameLogic()

    async def test_start_game__not_enough_players(self, player):
        room = await game_manager.create_room(
            owner=player, max_players=10, room_name=None, is_private=False
        )

        with pytest.raises(Exception) as e:
            await self.logic.start_game(room_id=room.id)

        assert "Not enough players" in str(e.value)

    async def test_start_game(
        self, player, people, mock_meme_cards, mock_situation_cards
    ):
        room = await game_manager.create_room(
            owner=player, max_players=10, is_private=False, room_name=None
        )
        for person in people:
            await game_manager.join_room(room.id, person)

        with patch(
            "app.services.memes_services.CardService.MEME_CARDS", mock_meme_cards
        ), patch(
            "app.services.situations_services.CardService.SITUATION_CARDS",
            mock_situation_cards,
        ):
            game = await self.logic.start_game(room_id=room.id)

        assert room.id in game_manager.active_games
        assert game.meme_deck != []
        assert game.situation_deck != []
        assert game.current_round
        for player in game.room.players:
            assert len(player.handed_cards) == 6
