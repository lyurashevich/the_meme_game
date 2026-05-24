import asyncio
from asyncio import Lock, Task
from dataclasses import dataclass, field
from datetime import datetime, timezone

from starlette.websockets import WebSocket

from app.exceptions import (
    GameNotFoundException,
    PlayerNotFoundException,
    RoomNotFoundException,
)
from app.game.dataclasses import Game, Player, Room
from app.game.enums import WebsocketEvents
from app.schemas.messages import ChatMessageResponse

RECONNECT_TIMEOUT = 60  # seconds


@dataclass
class GameManager:
    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    active_rooms: dict[str, Room] = field(default_factory=dict)  # room_id -> Room
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    player_sockets: dict[str, WebSocket | None] = field(default_factory=dict)  # player_id -> Websocket
    players: dict[str, Player] = field(default_factory=dict)  # player_id -> Player
    room_locks: dict[str, Lock] = field(default_factory=dict)  # room_id -> Lock
    room_tasks: dict[str, dict[str, Task]] = field(default_factory=dict)  # room_id -> {task_name -> Task}

    async def add_timer(self, room_id: str, name: str, task: Task) -> None:
        self.room_tasks.setdefault(room_id, {})

        old_task = self.room_tasks[room_id].get(name)
        if old_task and not old_task.done():
            old_task.cancel()

        self.room_tasks[room_id][name] = task

    def get_game(self, room_id: str) -> Game:
        game = self.active_games.get(room_id)

        if not game:
            raise GameNotFoundException()

        return game

    def get_player(self, player_id: str) -> Player:
        player = self.players.get(player_id)

        if not player:
            raise PlayerNotFoundException()

        return player

    def get_player_by_reconnect_token(self, reconnect_token: str) -> Player:
        player = next((player for player in self.players.values() if player.reconnect_token == reconnect_token), None)
        if not player:
            raise PlayerNotFoundException()
        return player

    def get_room(self, room_id: str) -> Room:
        room = self.active_rooms.get(room_id)

        if not room:
            raise RoomNotFoundException()

        return room

    def get_room_lock(self, room_id: str) -> Lock:
        lock = self.room_locks.get(room_id)

        if lock is None:
            raise Exception("Lock not found")

        return lock

    async def create_player(self, websocket: WebSocket | None = None, name: str | None = None) -> Player:
        player = Player(username=name)
        self.players[player.id] = player
        self.player_sockets[player.id] = websocket

        return player

    async def disconnect(self, player_id) -> None:
        room_id = self.player_connections.get(player_id)
        player = self.get_player(player_id)

        async def mark_disconnected():
            self.player_sockets[player_id] = None
            player.is_connected = False
            player.disconnected_at = datetime.now(timezone.utc)

        if room_id:
            async with self.get_room_lock(room_id):
                await mark_disconnected()
        else:
            await mark_disconnected()

        asyncio.create_task(self.players_cleanup(player_id))

    async def players_cleanup(self, player_id: str):
        await asyncio.sleep(RECONNECT_TIMEOUT)

        try:
            player = self.get_player(player_id)

            if player.is_connected:
                return

            if player.room_id:
                await self.leave_room(player_id)

            self.players.pop(player_id, None)
            self.player_sockets.pop(player_id, None)

        except PlayerNotFoundException:
            return

    async def send_personal_message(self, player_id: str, message: str) -> None:
        ws = self.player_sockets.get(player_id)
        if ws:
            await ws.send_text(message)

    async def broadcast_to_room(self, room_id: str, message: dict, sender_id: str | None = None) -> None:
        room = self.get_room(room_id=room_id)

        for player in room.players:
            if sender_id and player.id == sender_id:
                continue
            ws = self.player_sockets.get(player.id)
            if ws:
                await ws.send_json(message)

    async def send_chat_message(self, room_id: str, player_id: str, message: str):
        player = self.get_player(player_id)

        chat_message = {
            "player_id": player_id,
            "player_name": player.username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "room_id": room_id,
        }

        response_message = ChatMessageResponse(
            player_id=player_id,
            player_name=player.username,
            message=message,
            timestamp=chat_message["timestamp"],
            room_id=room_id,
        )

        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)
            room.messages.append(chat_message)

            sockets = [
                self.player_sockets.get(player.id) for player in room.players if self.player_sockets.get(player.id)
            ]

        for socket in sockets:
            if socket:
                await socket.send_json(response_message.model_dump())

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
        self.room_locks[room.id] = Lock()
        owner.room_id = room.id

        return room

    async def join_room(self, room_id: str, player: Player) -> None:
        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)

            await room.add_player(player)
            self.players[player.id] = player
            self.player_connections[player.id] = room_id
            player.room_id = room_id

        await self.broadcast_to_room(
            room_id=room_id,
            message={
                "event": WebsocketEvents.PLAYER_JOINED.value,
                "data": {"player_id": player.id, "username": player.username},
            },
            sender_id=player.id,
        )

    async def leave_room(self, player_id: str) -> None:
        player = self.get_player(player_id)
        need_cleanup = False

        room_id = self.player_connections[player_id]
        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)

            await room.remove_player(player)
            del self.player_connections[player_id]
            player.room_id = None
            if not room.players:
                need_cleanup = True

        if need_cleanup:
            await self.cleanup_room(room_id)

    async def cleanup_room(self, room_id) -> None:
        if room_id in self.active_games:
            del self.active_games[room_id]

        if room_id in self.active_rooms:
            del self.active_rooms[room_id]

        if room_id in self.room_locks:
            del self.room_locks[room_id]

        players_to_remove = [player_id for player_id, room in self.player_connections.items() if room == room_id]
        for player_id in players_to_remove:
            del self.player_connections[player_id]

    async def handle_reconnect(self, websocket: WebSocket, reconnection_token: str, now: datetime) -> Player:
        player = self.get_player_by_reconnect_token(reconnection_token)
        if not player:
            raise PlayerNotFoundException()

        if not player.disconnected_at or (now - player.disconnected_at).total_seconds() >= RECONNECT_TIMEOUT:
            raise PlayerNotFoundException()

        async def mark_reconnected():
            player.is_connected = True
            player.disconnected_at = None
            self.player_sockets[player.id] = websocket

        room_id = player.room_id

        if room_id:
            async with self.get_room_lock(room_id):
                await mark_reconnected()
        else:
            await mark_reconnected()

        return player


_game_manager = None


def get_game_manager():
    global _game_manager
    if _game_manager is None:
        _game_manager = GameManager()
    return _game_manager
