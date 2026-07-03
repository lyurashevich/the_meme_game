from app.exceptions import PlayerNotFoundException
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from app.models import MemeCard
from app.schemas.players import PlayerProfileUpdateSchema
from app.services.room_service import RoomService


class PlayerService:
    players: dict[str, Player] = {}  # player_id -> Player

    def __init__(self, connection_manager: ConnectionManager, room_service: RoomService):
        self.connection_manager = connection_manager
        self.room_service = room_service

    def create_player(self, username: str | None = None) -> Player:
        player = Player(username=username)
        self.players[player.id] = player

        return player

    def get_player_cards(self, player_id: str) -> list[MemeCard]:
        player = self.get_player(player_id)
        return player.handed_cards

    def add_player(self, player_id: str) -> None:
        player = self.get_player(player_id)
        self.players[player_id] = player

    def get_player(self, player_id: str) -> Player:
        player = self.players.get(player_id)

        if not player:
            raise PlayerNotFoundException()

        return player

    async def update_player_profile(self, player_id: str, data: PlayerProfileUpdateSchema) -> Player:
        player = self.get_player(player_id)

        if data.username:
            player.username = data.username

        if not player.room_id:
            await self.connection_manager.send_personal_json(
                player_id,
                {"event": WebsocketEvents.PLAYER_PROFILE_UPDATED.value, "payload": {"username": player.username}},
            )
        else:
            room = self.room_service.get_room(player.room_id)
            await self.connection_manager.broadcast_to_players(
                [player.id for player in room.players],
                {
                    "event": WebsocketEvents.PLAYER_PROFILE_UPDATED.value,
                    "username": player.username,
                    "player_id": player.id,
                },
            )

        return player
