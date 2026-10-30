"""The single place that pushes state to clients.

Services change state and then tell the notifier what happened ("room X changed",
"the winner was chosen"); the notifier builds fresh snapshots and sends them.
Never call it while holding a room lock: sending is network I/O.
"""

import asyncio

from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.services.player_service import PlayerService
from app.services.room_service import RoomService
from app.services.snapshots import (
    build_room_state,
    build_rooms_list,
    build_session,
)


class Notifier:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        room_service: RoomService,
        game_manager: GameManager,
        player_service: PlayerService,
    ):
        self.connection_manager = connection_manager
        self.room_service = room_service
        self.game_manager = game_manager
        self.player_service = player_service
        # Messages for one room go out one batch at a time, so a client can never receive
        # an older snapshot after a newer one (each batch is built when its turn comes).
        self._room_send_locks: dict[str, asyncio.Lock] = {}
        self._rooms_list_lock = asyncio.Lock()

    def _room_lock(self, room_id: str) -> asyncio.Lock:
        return self._room_send_locks.setdefault(room_id, asyncio.Lock())

    async def _send(self, player_id: str, event: WebsocketEvents, payload: dict | list) -> None:
        await self.connection_manager.send_personal_json(player_id, {"event": event.value, "payload": payload})

    async def send_session(self, player: Player, reconnect_token: str) -> None:
        await self._send(player.id, WebsocketEvents.SESSION, build_session(player, reconnect_token))

    async def send_event(self, player_id: str, event: WebsocketEvents, payload: dict) -> None:
        await self._send(player_id, event, payload)

    async def broadcast_event(self, room_id: str, event: WebsocketEvents, payload: dict) -> None:
        """A one-off event (winner chosen, game ended, chat message) for everyone in the room."""
        async with self._room_lock(room_id):
            room = await self.room_service.rooms.get(room_id)
            if room is None:
                return

            for player_id in [p.id for p in room.players]:
                await self._send(player_id, event, payload)

    async def broadcast_room_state(self, room_id: str, with_chat_for: str | None = None) -> None:
        """Send every player in the room their own up-to-date snapshot.

        ``with_chat_for`` adds the chat history to that player's snapshot (they just
        joined or reconnected and haven't seen it).
        """
        async with self._room_lock(room_id):
            room = await self.room_service.rooms.get(room_id)
            if room is None:
                self._room_send_locks.pop(room_id, None)
                return

            game = await self.game_manager.games.get(room_id)
            snapshots = [
                (p.id, build_room_state(room, game, p, chat=room.messages if p.id == with_chat_for else None))
                for p in room.players
            ]

            for player_id, snapshot in snapshots:
                await self._send(player_id, WebsocketEvents.ROOM_STATE, snapshot)

    async def broadcast_rooms_list(self) -> None:
        """Send the room list to every connected player who is not in a room."""
        async with self._rooms_list_lock:
            rooms_list = await self._build_rooms_list()

            for player_id in list(self.connection_manager.player_sockets):
                player = await self.player_service.players.get(player_id)
                if player and not player.room_id:
                    await self._send(player_id, WebsocketEvents.ROOMS_LIST, rooms_list)

    async def send_rooms_list(self, player_id: str) -> None:
        await self._send(player_id, WebsocketEvents.ROOMS_LIST, await self._build_rooms_list())

    async def _build_rooms_list(self) -> list[dict]:
        rooms = await self.room_service.get_rooms_list()
        games = {room.id: await self.game_manager.games.get(room.id) for room in rooms}
        return build_rooms_list(rooms, games)
