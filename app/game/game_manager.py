from dataclasses import dataclass, field
from datetime import datetime

from starlette.websockets import WebSocket

from app.game.dataclasses import Game, Player, Room
from app.schemas.messages import ChatMessageResponse


@dataclass
class GameManager:

    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    active_rooms: dict[str, Room] = field(default_factory=dict)  # room_id -> Room
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    player_sockets: dict[str, WebSocket] = field(default_factory=dict)  # player_id -> Websocket
    players: dict[str, Player] = field(default_factory=dict)  # player_id -> Player

    async def get_player(self, player_id: str) -> Player | None:
        player = self.players.get(player_id)
        if not player:
            raise Exception("Player not found")
        return player

    async def get_room(self, room_id: str) -> Room | None:
        room = self.active_rooms.get(room_id)
        if not room:
            raise Exception("Room not found")
        return room

    async def create_player(self, websocket: WebSocket | None = None, name: str | None = None) -> Player:
        player = Player(username=name)
        self.players[player.id] = player
        self.player_sockets[player.id] = websocket

        return player

    async def disconnect(self, player_id) -> None:
        self.player_sockets.pop(player_id, None)

    async def send_personal_message(self, player_id: str, message: str) -> None:
        ws = self.player_sockets.get(player_id)
        if ws:
            await ws.send_text(message)

    async def broadcast_to_room(self, room_id: str, message: str, sender_id: str | None = None) -> None:
        room = await self.get_room(room_id=room_id)

        for player in room.players:
            if sender_id and player.id == sender_id:
                continue
            ws = self.player_sockets.get(player.id)
            if ws:
                await ws.send_text(message)

    async def send_chat_message(self, room_id: str, player_id: str, message: str):
        room = await self.get_room(room_id=room_id)

        player = await self.get_player(player_id)

        chat_message = {
            "player_id": player_id,
            "player_name": player.username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "room_id": room_id,
        }
        room.messages.append(chat_message)

        response_message = ChatMessageResponse(
            player_id=player_id,
            player_name=player.username,
            message=message,
            timestamp=chat_message["timestamp"],
            room_id=room_id,
        )

        for player in room.players:
            ws = self.player_sockets.get(player.id)
            if ws:
                await ws.send_json(response_message.model_dump())

    def get_room_players_count(self, room_id: str) -> int:
        room = self.active_rooms.get(room_id)
        return len(room.players) if room else 0

    async def create_room(
        self,
        owner: Player,
        room_name: str | None = None,
        max_players: int = 10,
        is_private: bool = False,
    ) -> Room:
        room = Room(owner=owner, name=room_name, max_players=max_players, is_private=is_private)

        self.active_rooms[room.id] = room
        self.player_connections[owner.id] = room.id

        return room

    async def join_room(self, room_id: str, player: Player) -> None:
        room = await self.get_room(room_id=room_id)

        await room.add_player(player)
        self.players[player.id] = player
        self.player_connections[player.id] = room_id

    async def leave_room(self, player_id: str) -> None:
        player = await self.get_player(player_id)

        room_id = self.player_connections[player_id]
        room = await self.get_room(room_id=room_id)

        await room.remove_player(player)
        del self.player_connections[player_id]

        if not room.players:
            await self.cleanup_room(room_id)

    async def cleanup_room(self, room_id) -> None:
        if room_id in self.active_games:
            del self.active_games[room_id]

        if room_id in self.active_rooms:
            del self.active_rooms[room_id]

        players_to_remove = [player_id for player_id, room in self.player_connections.items() if room == room_id]
        for player_id in players_to_remove:
            del self.player_connections[player_id]


game_manager = GameManager()


def get_game_manager():
    return game_manager
