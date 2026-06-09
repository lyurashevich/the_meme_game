import asyncio
import secrets
from asyncio import Lock, Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.exceptions import (
    GameNotFoundException,
    InvalidReconnectToken,
    PlayerNotFoundException,
    RoomNotFoundException,
)
from app.game.dataclasses import Game, Player, ReconnectToken, Room
from app.game.enums import RoundState, WebsocketEvents
from app.game.websocket_sender import WebSocketSender
from app.schemas.messages import ChatMessageResponse

RECONNECT_TIMEOUT = 60  # seconds
RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


@dataclass
class GameManager:
    websocket_sender: WebSocketSender | None = None
    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    active_rooms: dict[str, Room] = field(default_factory=dict)  # room_id -> Room
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    players: dict[str, Player] = field(default_factory=dict)  # player_id -> Player
    room_locks: dict[str, Lock] = field(default_factory=dict)  # room_id -> Lock
    room_tasks: dict[str, dict[str, Task]] = field(default_factory=dict)  # room_id -> {task_name -> Task}

    # reconnect token storage (in-memory)
    # token -> ReconnectToken(player_id: str, expires_at: datetime (UTC, tz-aware)
    reconnect_tokens: dict[str, ReconnectToken] = field(default_factory=dict)
    # lock protecting reconnect_tokens
    reconnect_lock: Lock = field(default_factory=Lock)

    async def phase_timer(self, room_id: str):

        # print(
        #     f"round state before timer: {self.get_game(room_id).current_round.state
        #     if self.get_game(room_id).current_round else None}")
        await asyncio.sleep(30)
        # print(f"Phase timeout for room {room_id}")

        async with self.get_room_lock(room_id):
            game = self.get_game(room_id)
            room = self.get_room(room_id)

            if not game:
                return

            # Perform phase transition logic here, e.g.:
            if game.current_round:
                if game.current_round.state == RoundState.CHOOSING_CARDS:
                    game.current_round.state = RoundState.LEADER_CHOOSING

                    if self.websocket_sender is None:
                        raise RuntimeError("WebSocketSender not configured")

                    await self.websocket_sender.send_round_state_changed(room, RoundState.LEADER_CHOOSING.value)
                    print(f"round state after timer: {game.current_round.state}")
                elif game.current_round.state == RoundState.LEADER_CHOOSING:
                    game.current_round.state = RoundState.ROUND_ENDED

                    if self.websocket_sender is None:
                        raise RuntimeError("WebSocketSender not configured")

                    await self.websocket_sender.send_round_state_changed(room, RoundState.ROUND_ENDED.value)
                    print(f"round state after timer: {game.current_round.state}")
                else:
                    return  # No transition needed

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

    # def get_player_by_reconnect_token(self, reconnect_token: str) -> Player:
    #     token = self.reconnect_tokens.get(reconnect_token)
    #     player = self.get_player(token.player_id)
    #     if not player:
    #         raise PlayerNotFoundException()
    #     return player

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

    async def create_player(self, name: str | None = None) -> Player:
        player = Player(username=name)
        self.players[player.id] = player

        return player

    async def disconnect(self, player_id) -> None:
        # mark player disconnected asap to avoid races with other flows
        player = self.get_player(player_id)

        async def mark_disconnected():
            player.is_connected = False

        # perform immediate state update without relying on room lock; room-specific
        # operations (if any in future) should acquire room lock separately.
        await mark_disconnected()

        # create reconnect token so player may reconnect within TTL
        try:
            token = next(value for key, value in self.reconnect_tokens.items() if value.player_id == player_id)
            token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)
            # await self.create_reconnect_token(player_id, datetime.now(timezone.utc))
        except Exception:  # nosec B110
            # todo: add logging
            # if anything goes wrong, ignore token creation — disconnection proceeds
            pass

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

            # Clean up any reconnect tokens for this player
            # to prevent memory leak and invalid token consumption
            await self._cleanup_player_tokens(player_id)

        except PlayerNotFoundException:
            return

    async def send_chat_message(self, room_id: str, player_id: str, message: str, connection_manager) -> None:
        # Get player first (caller guarantees player_id is valid from WebSocket)
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

            sockets = [player.id for player in room.players]

        await connection_manager.broadcast_to_room(sockets, response_message.model_dump())

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

    async def join_room(self, room_id: str, player: Player, connection_manager) -> None:
        async with self.get_room_lock(room_id):
            room = self.get_room(room_id=room_id)

            await room.add_player(player)
            self.players[player.id] = player
            self.player_connections[player.id] = room_id
            player.room_id = room_id

        await connection_manager.broadcast_to_room(
            [player.id for player in room.players],
            {
                "event": WebsocketEvents.PLAYER_JOINED.value,
                "data": {"player_id": player.id, "username": player.username},
            },
            exclude_id=player.id,
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

    # ========== Reconnect token helpers (in-memory) ==========
    async def create_reconnect_token(self, player_id: str) -> str:
        """
        Create a one-time reconnect token for a player.
        TTL starts from 'now' (UTC). Returns the token.
        """
        token = secrets.token_hex(16)
        # TTL is specified in seconds
        async with self.reconnect_lock:
            self.reconnect_tokens[token] = ReconnectToken(player_id=player_id, expires_at=None)

        return token

    async def consume_reconnect_token(self, token: str, now: datetime) -> str:
        """
        Consume a reconnect token and return associated player_id.
        If token missing or expired -> raise InvalidReconnectToken.
        Token is deleted on consumption or when expired.

        IMPORTANT: Player existence is checked INSIDE the lock to prevent
        race conditions where player is deleted between token check and return.
        """
        async with self.reconnect_lock:
            entry = self.reconnect_tokens.get(token)
            if not entry:
                raise InvalidReconnectToken()

            if not entry.expires_at:
                raise Exception("expires at error")

            if entry.expires_at < now:
                # expired token: try to clear player's attribute if player still exists
                try:
                    self.get_player(entry.player_id)
                except PlayerNotFoundException:
                    # player already removed - nothing to clear
                    pass
                # remove token mapping
                del self.reconnect_tokens[token]
                raise InvalidReconnectToken()

            player_id = entry.player_id
            # Verify player still exists BEFORE removing token (critical!)
            try:
                self.get_player(player_id)
            except PlayerNotFoundException:
                # Player was deleted - treat as invalid token
                del self.reconnect_tokens[token]
                raise InvalidReconnectToken()

            # one-time token: remove it (only if player exists)
            del self.reconnect_tokens[token]

        return player_id

    # background cleaner for expired reconnect tokens
    async def _reconnect_cleanup_loop(self, interval_seconds: int = 30):
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                await self.cleanup_expired_tokens()
            except asyncio.CancelledError:
                break
            except Exception:  # nosec B110
                # todo: add logging
                # ignore exceptions in background cleanup
                pass

    def start_reconnect_cleaner(self, interval_seconds: int = 30) -> None:
        # start background cleanup if event loop is running
        if getattr(self, "_reconnect_cleanup_task", None) is None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._reconnect_cleanup_task = asyncio.create_task(self._reconnect_cleanup_loop(interval_seconds))
            except RuntimeError:
                # no running loop - caller should start cleaner later if needed
                pass

    async def cleanup_expired_tokens(self, now: datetime | None = None) -> None:
        """
        Remove all expired reconnect tokens. Can be scheduled periodically.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        async with self.reconnect_lock:
            expired = [t for t, e in self.reconnect_tokens.items() if e.expires_at and e.expires_at < now]
            for t in expired:
                del self.reconnect_tokens[t]

    async def _cleanup_player_tokens(self, player_id: str) -> None:
        """
        Remove all reconnect tokens for a specific player.
        Called when player is permanently deleted.
        """
        async with self.reconnect_lock:
            tokens_to_remove = [token for token, entry in self.reconnect_tokens.items() if entry.player_id == player_id]
            for token in tokens_to_remove:
                del self.reconnect_tokens[token]

    # handle_reconnect now uses token storage + TTL checks
    async def handle_reconnect(self, reconnection_token: str, now: datetime) -> Player:
        """
        Reconnect a player using their token.

        Raises:
            PlayerNotFoundException: if token invalid/expired/player not found
        """
        # Validate and consume token (raises InvalidReconnectToken if invalid/expired)
        # This also checks that player exists at token consumption time
        try:
            player_id = await self.consume_reconnect_token(reconnection_token, now)
        except InvalidReconnectToken:
            raise PlayerNotFoundException()

        # At this point we know player exists (checked inside consume_reconnect_token)
        player = self.get_player(player_id)

        async def mark_reconnected():
            player.is_connected = True

        room_id = player.room_id

        if room_id:
            async with self.get_room_lock(room_id):
                await mark_reconnected()
        else:
            await mark_reconnected()

        return player
