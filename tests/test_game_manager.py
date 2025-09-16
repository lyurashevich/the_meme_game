import pytest

from app.game.dataclasses import Player
from app.game.game_manager import game_manager


class TestGameManager:

    async def test_create_room(self, player) -> None:
        room = await game_manager.create_room(room_name=None, owner=player)

        assert room.id in game_manager.active_rooms
        assert player.id in game_manager.player_connections

    async def test_join_room(self, player):
        room = await game_manager.create_room(room_name=None, owner=player)

        player1 = Player(id=333)
        await game_manager.join_room(room.id, player1)

        assert player1.id in game_manager.player_connections

    async def test_join_room__already_joined(self, player):
        room = await game_manager.create_room(room_name=None, owner=player)

        with pytest.raises(Exception) as e:
            await game_manager.join_room(room.id, player)

        assert "You have already joined" in str(e.value)

    async def test_join_room__room_not_found(self, player):
        with pytest.raises(Exception) as e:
            await game_manager.join_room("abc", player)

        assert "Room not found" in str(e.value)

    async def test_join_room__full_room(self, player):
        room = await game_manager.create_room(
            owner=player, max_players=1, room_name=None, is_private=False
        )
        player1 = Player(id=555)

        with pytest.raises(Exception) as e:
            await game_manager.join_room(room.id, player1)

        assert "The room is full" in str(e.value)
        assert player1.id not in game_manager.player_connections

    async def test_leave_room(self, player):
        room = await game_manager.create_room(
            owner=player, room_name=None, max_players=10, is_private=False
        )
        player1 = Player(id=555)
        await game_manager.join_room(room.id, player1)
        await game_manager.leave_room(player1.id)

        assert player.id in game_manager.player_connections
        assert player1.id not in game_manager.player_connections
