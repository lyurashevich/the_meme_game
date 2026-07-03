from asyncio import Lock

from app.exceptions import RoomNotFoundException
from app.game.dataclasses import Player, Room


class RoomService:
    active_rooms: dict[str, Room] = {}  # room_id -> Room
    room_locks: dict[str, Lock] = {}  # room_id -> Lock

    def get_rooms_list(self) -> list[Room]:
        return list(self.active_rooms.values())

    def get_room(self, room_id: str) -> Room:
        room = self.active_rooms.get(room_id)

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

        self.active_rooms[room.id] = room
        self.room_locks[room.id] = Lock()
        owner.room_id = room.id

        return room

    async def join_room(self, room_id: str, player: Player) -> None:
        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)

            room.add_player(player)
            player.room_id = room_id

    async def leave_room(self, player: Player, room_id: str) -> None:
        need_cleanup = False

        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)

            room.remove_player(player)
            player.room_id = None
            if not room.players:
                need_cleanup = True

        if need_cleanup:
            await self.cleanup_room(room_id)

    async def cleanup_room(self, room_id) -> None:
        # if room_id in self.active_games:
        #     del self.active_games[room_id]

        if room_id in self.active_rooms:
            del self.active_rooms[room_id]

        if room_id in self.room_locks:
            del self.room_locks[room_id]

        # players_to_remove = [player_id for player_id, room in self.player_connections.items() if room == room_id]
        # for player_id in players_to_remove:
        #     del self.player_connections[player_id]

    async def update_room(self):
        pass
