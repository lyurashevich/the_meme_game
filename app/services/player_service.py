import asyncio

from app.exceptions import PlayerNotFoundException
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from app.models import MemeCard
from app.repositories.base import PlayerRepository
from app.schemas.players import BasePlayerProfileSchema
from app.services.room_service import RoomService

RECONNECT_TIMEOUT = 60  # seconds


class PlayerService:
    def __init__(self, players: PlayerRepository, connection_manager: ConnectionManager, room_service: RoomService):
        self.players = players
        self.connection_manager = connection_manager
        self.room_service = room_service

    async def players_cleanup(self, player_id: str, connection_manager):
        await asyncio.sleep(RECONNECT_TIMEOUT)

        try:
            player = await self.get_player(player_id)

            if player.is_connected:
                return

            if player.room_id:
                await self.room_service.leave_room(player, player.room_id)

            await self.players.remove(player_id)

            # Clean up any reconnect tokens for this player
            # to prevent memory leak and invalid token consumption
            await self._cleanup_player_tokens(player_id)  # type: ignore  # todo: подумать че с этим делать......

        except PlayerNotFoundException:
            return

    async def create_player(self, username: str = "") -> Player:
        player = Player(username=username)
        await self.players.add(player)

        return player

    async def get_players(self) -> list[Player]:
        return await self.players.list()

    async def get_player_cards(self, player_id: str) -> list[MemeCard]:
        player = await self.get_player(player_id)
        return player.hand_cards

    async def add_player(self, player_id: str) -> None:
        player = await self.get_player(player_id)
        await self.players.add(player)

    async def get_player(self, player_id: str) -> Player:
        player = await self.players.get(player_id)

        if not player:
            raise PlayerNotFoundException()

        return player

    async def update_player_profile(self, player_id: str, data: BasePlayerProfileSchema) -> Player:
        player = await self.get_player(player_id)

        if data.username:
            player.username = data.username

        if not player.room_id:
            await self.connection_manager.send_personal_json(
                player_id,
                {"event": WebsocketEvents.PLAYER_PROFILE_UPDATED.value, "payload": {"username": player.username}},
            )
        else:
            room = await self.room_service.get_room(player.room_id)
            await self.connection_manager.broadcast_to_players(
                [player.id for player in room.players],
                {
                    "event": WebsocketEvents.PLAYER_PROFILE_UPDATED.value,
                    "username": player.username,
                    "player_id": player.id,
                },
            )

        return player
