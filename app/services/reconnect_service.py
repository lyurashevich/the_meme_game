import asyncio
import logging
import secrets
from asyncio import Lock, Task
from datetime import datetime, timedelta, timezone

from app.exceptions import (
    InvalidReconnectToken,
    PlayerNotInRoomException,
    RoomNotFoundException,
)
from app.game.dataclasses import Player, ReconnectToken
from app.repositories.base import ReconnectTokenRepository
from app.services.game_service import GameService
from app.services.player_service import PlayerService

logger = logging.getLogger(__name__)

# How long a disconnected player has to come back. Their reconnect token expires and,
# if they haven't returned, they are removed - both after this same time.
RECONNECT_TOKEN_TTL_SECONDS = 60


class ReconnectService:
    def __init__(self, tokens: ReconnectTokenRepository, player_service: PlayerService, game_service: GameService):
        self.tokens = tokens
        self.player_service = player_service
        self.game_service = game_service
        self.reconnect_lock = Lock()
        self.reconnect_timeout: float = RECONNECT_TOKEN_TTL_SECONDS  # overridable, e.g. in tests
        # asyncio tasks are bound to this process's event loop, so they stay local
        self._removal_tasks: dict[str, Task] = {}  # player_id -> pending removal

    async def create_reconnect_token(self, player_id: str) -> str:
        async with self.reconnect_lock:
            old = await self.tokens.get_token_for_player(player_id)
            if old:
                await self.tokens.remove(old)

            token = secrets.token_hex(16)
            # no expiry while connected; disconnect() starts the countdown
            await self.tokens.add(token, ReconnectToken(player_id=player_id, expires_at=None))

            return token

    async def _consume_reconnect_token(self, token: str, now: datetime) -> str:
        async with self.reconnect_lock:
            return await self._consume_reconnect_token_locked(token, now)

    async def _consume_reconnect_token_locked(self, token: str, now: datetime) -> str:
        entry = await self.tokens.remove(token)

        if not entry:
            raise InvalidReconnectToken()

        if entry.expires_at and entry.expires_at < now:
            raise InvalidReconnectToken()

        return entry.player_id

    async def disconnect(self, player_id) -> None:
        """The player's connection is gone: give them ``reconnect_timeout`` seconds to come back."""
        async with self.reconnect_lock:
            player = await self.player_service.get_player(player_id)
            player.is_connected = False

            token = await self.tokens.get_token_for_player(player_id)
            entry = await self.tokens.get(token) if token else None
            if token and entry:
                entry.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.reconnect_timeout)
                await self.tokens.add(token, entry)

        self._schedule_removal(player_id)

    async def handle_reconnect(self, reconnection_token: str, now: datetime) -> Player:
        # Under the same lock remove_player checks is_connected and drops the token: either the
        # player is back before the removal starts (and it does nothing), or the token is gone.
        async with self.reconnect_lock:
            player_id = await self._consume_reconnect_token_locked(reconnection_token, now)
            player = await self.player_service.get_player(player_id)
            player.is_connected = True

        self._cancel_removal(player_id)

        return player

    def _schedule_removal(self, player_id: str) -> None:
        self._cancel_removal(player_id)
        self._removal_tasks[player_id] = asyncio.create_task(self._remove_after_timeout(player_id))

    def _cancel_removal(self, player_id: str) -> None:
        task = self._removal_tasks.pop(player_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()

    async def _remove_after_timeout(self, player_id: str) -> None:
        await asyncio.sleep(self.reconnect_timeout)

        # Time is up: from here on the removal must not be cancelled halfway through leaving the
        # room, so it stops being a "pending removal" that a reconnect would cancel.
        if self._removal_tasks.get(player_id) is asyncio.current_task():
            del self._removal_tasks[player_id]

        try:
            await self.remove_player(player_id)
        except Exception:
            # nobody awaits this task, so the error would otherwise be lost
            logger.exception("Failed to remove disconnected player %s", player_id)

    async def remove_player(self, player_id: str) -> None:
        """Remove a player who didn't come back: leave their room the regular way (the game reacts as
        to any leave - a new round if they led, the end of the game if too few players remain), then
        forget them and their token."""
        async with self.reconnect_lock:
            player = await self.player_service.players.get(player_id)
            if player is None or player.is_connected:
                return  # already gone, or back in time

            # from now on they can't come back as this player
            token = await self.tokens.get_token_for_player(player_id)
            if token:
                await self.tokens.remove(token)

        if player.room_id:
            try:
                await self.game_service.process_leave(player, player.room_id, confirm=True)
            except (RoomNotFoundException, PlayerNotInRoomException):
                player.room_id = None  # the room is gone already

        await self.player_service.players.remove(player_id)

    async def cleanup_expired_tokens(self):
        now = datetime.now(timezone.utc)

        async with self.reconnect_lock:
            for token, entry in await self.tokens.list():
                if entry.expires_at and entry.expires_at < now:
                    await self.tokens.remove(token)
