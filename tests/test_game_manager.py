import pytest

from app.exceptions import RoomNotFoundException
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
    async def test_create_room(
        self, test_player, room_name, max_players, is_private, room_service, game_manager
    ) -> None:
        room = await room_service.create_room(
            room_name=room_name,
            max_players=max_players,
            is_private=is_private,
            owner=test_player,
        )

        assert room.id in room_service.active_rooms
        assert room.name == room_name
        assert room.max_players == max_players
        assert room.is_private == is_private

    async def test_create_room__blank_name(self, test_player, room_service):
        room = await room_service.create_room(owner=test_player)

        assert room.id in room_service.active_rooms
        assert room.name.startswith("room")

    async def test_join_room(self, test_room, room_service):

        player = Player(id="333")
        await room_service.join_room(test_room.id, player)

        assert player in test_room.players

    async def test_join_room__already_joined(self, test_player, test_room, room_service):

        with pytest.raises(Exception) as e:
            await room_service.join_room(test_room.id, test_player)

        assert "You have already joined" in str(e.value)

    async def test_join_room__room_not_found(self, test_player, room_service):
        with pytest.raises(RoomNotFoundException) as e:
            await room_service.join_room("abc", test_player)

        assert "Room not found" in str(e.value.message)

    async def test_join_room__full_room(self, test_room, room_service, game_manager):
        test_room.max_players = 1
        player = Player(id="555")

        with pytest.raises(Exception) as e:
            await room_service.join_room(test_room.id, player)

        assert "The room is full" in str(e.value)
        assert player.id not in game_manager.player_connections

    async def test_leave_room(self, test_player, test_room, room_service, game_manager):
        player = Player(id="555")
        await room_service.join_room(test_room.id, player)
        await room_service.leave_room(player, test_room.id)

        assert test_player in test_room.players
        assert player not in test_room.players
