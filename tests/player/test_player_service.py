from unittest.mock import AsyncMock

from app.game.enums import WebsocketEvents
from app.schemas.players import BasePlayerProfileSchema


class TestPlayerService:

    async def test_update_player_profile__no_room(self, test_player, player_service, connection_manager):
        new_username = "new"
        test_player.avatar_id = "avatar_id"
        test_player.room_id = None

        connection_manager.broadcast_to_players = AsyncMock()

        await player_service.players.add(test_player)

        await player_service.update_player_profile(test_player.id, BasePlayerProfileSchema(username=new_username))

        assert test_player.username == new_username
        assert test_player.avatar_id == "avatar_id"

        connection_manager.broadcast_to_players.assert_not_called()

    async def test_update_player_profile__in_room(
        self, test_player, connection_manager, game_manager, player_service, test_room, room_service
    ):
        new_username = "new"
        test_player.room_id = test_room.id
        room_service.get_room = AsyncMock()
        room_service.get_room.return_value = test_room
        test_room.players = [test_player]

        connection_manager.broadcast_to_players = AsyncMock()

        await player_service.players.add(test_player)

        await player_service.update_player_profile(test_player.id, BasePlayerProfileSchema(username=new_username))

        assert test_player.username == new_username

        connection_manager.broadcast_to_players.assert_called_once_with(
            [player.id for player in test_room.players],
            {
                "event": WebsocketEvents.PLAYER_PROFILE_UPDATED.value,
                "username": new_username,
                "player_id": test_player.id,
            },
        )
