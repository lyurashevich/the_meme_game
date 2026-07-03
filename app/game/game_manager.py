import asyncio
import secrets
from asyncio import Lock, Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.exceptions import (
    AlreadyInARoomException,
    GameNotFoundException,
    InvalidReconnectToken,
    PlayerNotFoundException,
)
from app.game.dataclasses import Game, Player, ReconnectToken
from app.schemas.messages import ChatMessageResponse

RECONNECT_TIMEOUT = 60  # seconds
RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


@dataclass
class GameManager:
    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    room_tasks: dict[str, dict[str, Task]] = field(default_factory=dict)  # room_id -> {task_name -> Task}

    # reconnect token storage (in-memory)
    # token -> ReconnectToken(player_id: str, expires_at: datetime (UTC, tz-aware)
    reconnect_tokens: dict[str, ReconnectToken] = field(default_factory=dict)
    # lock protecting reconnect_tokens
    reconnect_lock: Lock = field(default_factory=Lock)

    def delete_player_from_player_connections(self, player_id: str):
        del self.player_connections[player_id]

    def add_player_to_player_connections(self, player_id: str, room_id: str) -> None:
        self.player_connections[player_id] = room_id

    def validate_player_can_join_room(self, player_id: str) -> bool:
        if player_id in self.player_connections:
            raise AlreadyInARoomException()

        return True

    def get_game(self, room_id: str) -> Game:
        game = self.active_games.get(room_id)

        if not game:
            raise GameNotFoundException()

        return game

    async def disconnect(self, player_id, connection_manager) -> None:
        # mark player disconnected asap to avoid races with other flows
        player = self.get_player(player_id)  # type: ignore

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

        asyncio.create_task(self.players_cleanup(player_id, connection_manager))

    async def players_cleanup(self, player_id: str, connection_manager):
        await asyncio.sleep(RECONNECT_TIMEOUT)

        try:
            player = self.get_player(player_id)  # type: ignore

            if player.is_connected:
                return

            if player.room_id:
                await self.leave_room(player_id, connection_manager)  # type: ignore

            self.players.pop(player_id, None)  # type: ignore

            # Clean up any reconnect tokens for this player
            # to prevent memory leak and invalid token consumption
            await self._cleanup_player_tokens(player_id)

        except PlayerNotFoundException:
            return

    async def send_chat_message(self, room_id: str, player_id: str, message: str, connection_manager) -> None:
        # Get player first (caller guarantees player_id is valid from WebSocket)
        player = self.get_player(player_id)  # type: ignore

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

        async with self.get_room_lock(room_id):  # type: ignore
            room = self.get_room(room_id=room_id)  # type: ignore
            room.messages.append(chat_message)

            sockets = [player.id for player in room.players]

        await connection_manager.broadcast_to_players(sockets, response_message.model_dump())

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
                    self.get_player(entry.player_id)  # type: ignore
                except PlayerNotFoundException:
                    # player already removed - nothing to clear
                    pass
                # remove token mapping
                del self.reconnect_tokens[token]
                raise InvalidReconnectToken()

            player_id = entry.player_id
            # Verify player still exists BEFORE removing token (critical!)
            try:
                self.get_player(player_id)  # type: ignore
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
        player = self.get_player(player_id)  # type: ignore

        async def mark_reconnected():
            player.is_connected = True

        room_id = player.room_id

        if room_id:
            async with self.get_room_lock(room_id):  # type: ignore
                await mark_reconnected()
        else:
            await mark_reconnected()

        return player
