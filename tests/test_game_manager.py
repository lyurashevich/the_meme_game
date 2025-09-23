import pytest

from app.game.dataclasses import Player
from app.game.game_manager import get_game_manager


class TestGameManager:
    def setup_method(self):
        self.game_manager = get_game_manager()

    @pytest.mark.parametrize(
        "room_name, max_players, is_private",
        [
            ("Room 1", 4, True),
            ("Room 2", 10, False),
            ("", 2, True),
            ("Very Long Room Name That Should Still Work", 8, False),
        ],
    )
    async def test_create_room(self, test_player, room_name, max_players, is_private) -> None:
        room = await self.game_manager.create_room(
            room_name=room_name,
            max_players=max_players,
            is_private=is_private,
            owner=test_player,
        )

        assert room.id in self.game_manager.active_rooms
        assert test_player.id in self.game_manager.player_connections
        assert room.name == room_name
        assert room.max_players == max_players
        assert room.is_private == is_private

    async def test_create_room__blank_name(self, test_player):
        room = await self.game_manager.create_room(owner=test_player)

        assert room.id in self.game_manager.active_rooms
        assert room.name.startswith("room")

    async def test_join_room(self, test_room):

        player = Player(id="333")
        await self.game_manager.join_room(test_room.id, player)

        assert player.id in self.game_manager.player_connections

    async def test_join_room__already_joined(self, test_player, test_room):

        with pytest.raises(Exception) as e:
            await self.game_manager.join_room(test_room.id, test_player)

        assert "You have already joined" in str(e.value)

    async def test_join_room__room_not_found(self, test_player):
        with pytest.raises(Exception) as e:
            await self.game_manager.join_room("abc", test_player)

        assert "Room not found" in str(e.value)

    async def test_join_room__full_room(self, test_room):
        test_room.max_players = 1
        player = Player(id="555")

        with pytest.raises(Exception) as e:
            await self.game_manager.join_room(test_room.id, player)

        assert "The room is full" in str(e.value)
        assert player.id not in self.game_manager.player_connections

    async def test_leave_room(self, test_player, test_room):
        player = Player(id="555")
        await self.game_manager.join_room(test_room.id, player)
        await self.game_manager.leave_room(player.id)

        assert test_player.id in self.game_manager.player_connections
        assert player.id not in self.game_manager.player_connections
