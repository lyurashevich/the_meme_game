from asyncio import Lock
from datetime import datetime

from app.exceptions import PlayerNotInRoomException, RoomNotFoundException
from app.game.dataclasses import Player, Room
from app.game.enums import WebsocketEvents
from app.schemas.messages import ChatMessageResponse


class RoomService:
    active_rooms: dict[str, Room] = {}  # room_id -> Room
    room_locks: dict[str, Lock] = {}  # room_id -> Lock

    async def get_player(self, player_id: str, room_id: str) -> Player:
        async with self.get_room_lock(room_id):
            room = self.get_room(room_id)
            player = next((player for player in room.players if player.id == player_id), None)

            if not player:
                raise PlayerNotInRoomException()

            return player

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

            if room.owner is player and room.players:
                room.reassign_owner()

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

    @staticmethod
    def build_room_created_message(room: Room, audience: list[str]) -> tuple[list[str], dict]:
        return audience, {
            "event": WebsocketEvents.ROOM_CREATED.value,
            "payload": {"room_id": room.id, "room_name": room.name},
        }

    @staticmethod
    def build_join_room_messages(room: Room, player: Player) -> list[tuple[list[str], dict]]:
        you_joined = (
            [player.id],
            {
                "event": WebsocketEvents.YOU_JOINED_THE_ROOM.value,
                "payload": {
                    "room_id": room.id,
                    "room_name": room.name,
                    "players": [{"id": p.id, "username": p.username} for p in room.players],
                },
            },
        )
        other_player_ids = [p.id for p in room.players if p.id != player.id]
        player_joined = (
            other_player_ids,
            {
                "event": WebsocketEvents.PLAYER_JOINED_ROOM.value,
                "payload": {"player_id": player.id, "username": player.username},
            },
        )
        return [you_joined, player_joined]

    async def send_chat_message(self, room_id: str, player: Player, message: str) -> tuple[list[str], dict]:

        chat_message = {
            "player_id": player.id,
            "player_name": player.username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "room_id": room_id,
        }

        response_message = ChatMessageResponse(
            player_id=player.id,
            player_name=player.username,
            message=message,
            timestamp=chat_message["timestamp"],
            room_id=room_id,
        )

        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)
            room.messages.append(chat_message)

            sockets = [p.id for p in room.players]

        return sockets, response_message.model_dump()
