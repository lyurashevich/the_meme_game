import pytest

from app.dependencies import connection_manager, game_manager
from app.game.dataclasses import Player


class TestGameManager:
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
        room = await game_manager.create_room(
            room_name=room_name,
            max_players=max_players,
            is_private=is_private,
            owner=test_player,
        )

        assert room.id in game_manager.active_rooms
        assert test_player.id in game_manager.player_connections
        assert room.name == room_name
        assert room.max_players == max_players
        assert room.is_private == is_private

    async def test_create_room__blank_name(self, test_player):
        room = await game_manager.create_room(owner=test_player)

        assert room.id in game_manager.active_rooms
        assert room.name.startswith("room")

    async def test_join_room(self, test_room):

        player = Player(id="333")
        await game_manager.join_room(test_room.id, player, connection_manager)

        assert player.id in game_manager.player_connections

    async def test_join_room__already_joined(self, test_player, test_room):

        with pytest.raises(Exception) as e:
            await game_manager.join_room(test_room.id, test_player, connection_manager)

        assert "You have already joined" in str(e.value)

    @pytest.mark.skip
    async def test_join_room__room_not_found(self, test_player):
        with pytest.raises(Exception) as e:
            await game_manager.join_room("abc", test_player, connection_manager)

        assert "Room not found" in str(e.value)

    async def test_join_room__full_room(self, test_room):
        test_room.max_players = 1
        player = Player(id="555")

        with pytest.raises(Exception) as e:
            await game_manager.join_room(test_room.id, player, connection_manager)

        assert "The room is full" in str(e.value)
        assert player.id not in game_manager.player_connections

    async def test_leave_room(self, test_player, test_room):
        player = Player(id="555")
        await game_manager.join_room(test_room.id, player, connection_manager)
        await game_manager.leave_room(player.id)

        assert test_player.id in game_manager.player_connections
        assert player.id not in game_manager.player_connections
