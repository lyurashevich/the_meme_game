from app.exceptions import PlayerNotFoundException
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.game.websocket_sender import WebSocketSender
from app.schemas.players import PlayerProfileUpdateSchema


class PlayerService:
    def __init__(self, manager: "GameManager", sender: "WebSocketSender", connection_manager: "ConnectionManager"):
        self.manager = manager
        self.sender = sender
        self.connection_manager = connection_manager

    def get_player(self, player_id: str) -> Player:
        player = self.manager.players.get(player_id, None)

        if not player:
            raise PlayerNotFoundException()

        return player

    async def update_player_profile(self, player_id: str, data: PlayerProfileUpdateSchema) -> Player:
        player = self.get_player(player_id)

        if data.username:
            player.username = data.username

        if not player.room_id:
            await self.sender.send(
                player_id, WebsocketEvents.PLAYER_PROFILE_UPDATED.value, {"username": player.username}
            )
        else:
            room = self.manager.get_room(player.room_id)
            await self.connection_manager.broadcast_to_room(
                [player.id for player in room.players],
                {"event": WebsocketEvents.PLAYER_PROFILE_UPDATED, "username": player.username, "player_id": player.id},
            )

        return player
