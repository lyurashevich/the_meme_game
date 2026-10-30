from asyncio import Lock
from datetime import datetime, timezone

from app.exceptions import PlayerNotInRoomException, RoomNotFoundException
from app.game.dataclasses import Player, Room
from app.repositories.base import RoomRepository
from app.services.snapshots import CHAT_HISTORY_LIMIT


class RoomService:
    def __init__(self, rooms: RoomRepository):
        self.rooms = rooms
        self.room_locks: dict[str, Lock] = {}  # room_id -> Lock

    async def get_player(self, player_id: str, room_id: str) -> Player:
        async with self.get_room_lock(room_id):
            room = await self.get_room(room_id)
            player = next((player for player in room.players if player.id == player_id), None)

            if not player:
                raise PlayerNotInRoomException()

            return player

    async def get_rooms_list(self) -> list[Room]:
        return await self.rooms.list()

    async def get_room(self, room_id: str) -> Room:
        room = await self.rooms.get(room_id)

        if not room:
            raise RoomNotFoundException()

        return room

    def get_room_lock(self, room_id: str) -> Lock:
        """Get or create a lock for the room.

        Always returns a lock - auto-creates if not found (race-safe).
        This ensures async context manager won't fail mid-transaction.
        """
        if room_id not in self.room_locks:
            self.room_locks[room_id] = Lock()
        return self.room_locks[room_id]

    async def create_room(
        self, owner: Player, room_name: str | None = None, max_players: int = 10, is_private: bool = False
    ) -> Room:
        room = Room(owner=owner, name=room_name, max_players=max_players, is_private=is_private)

        await self.rooms.add(room)
        self.room_locks[room.id] = Lock()
        owner.room_id = room.id

        return room

    async def join_room(self, room_id: str, player: Player) -> None:
        async with self.get_room_lock(room_id):
            room = await self.get_room(room_id=room_id)

            room.add_player(player)
            player.room_id = room_id

    async def cleanup_room(self, room_id) -> None:
        """Forget the room itself. Its game and timers are GameService's to remove (see _remove_room_locked)."""
        await self.rooms.remove(room_id)

        if room_id in self.room_locks:
            del self.room_locks[room_id]

    async def update_room(self):
        pass

    async def add_chat_message(self, room_id: str, player: Player, text: str) -> dict:
        """Store a chat message (only the latest ``CHAT_HISTORY_LIMIT`` are kept) and return it."""
        message = {
            "player_id": player.id,
            "username": player.username,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with self.get_room_lock(room_id):
            room = await self.get_room(room_id=room_id)
            room.messages.append(message)
            del room.messages[:-CHAT_HISTORY_LIMIT]

        return message
