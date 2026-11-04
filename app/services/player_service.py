from app.exceptions import PlayerNotFoundException, UsernameTakenException
from app.game.dataclasses import Player
from app.models import MemeCard
from app.repositories.base import PlayerRepository
from app.schemas.players import BasePlayerProfileSchema
from app.services.room_service import RoomService


class PlayerService:
    def __init__(self, players: PlayerRepository, room_service: RoomService):
        self.players = players
        self.room_service = room_service

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
            await self._rename(player, data.username)

        if data.avatar_id:
            player.avatar_id = data.avatar_id

        return player

    async def _rename(self, player: Player, username: str) -> None:
        """Names are unique per room: inside a room, a name another player has is refused."""
        room = await self.room_service.rooms.get(player.room_id) if player.room_id else None
        if room is None:
            player.username = username
            return

        # under the room lock, so a player joining with the same name at the same moment can't slip in
        async with self.room_service.get_room_lock(room.id):
            if room.is_username_taken(username, by_other_than=player):
                raise UsernameTakenException()
            player.username = username
