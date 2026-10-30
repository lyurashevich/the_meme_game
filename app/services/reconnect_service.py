import secrets
from asyncio import Lock
from datetime import datetime, timedelta, timezone

from app.exceptions import InvalidReconnectToken
from app.game.dataclasses import Player, ReconnectToken
from app.repositories.base import ReconnectTokenRepository
from app.services.player_service import PlayerService

RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


class ReconnectService:
    def __init__(self, tokens: ReconnectTokenRepository, player_service: PlayerService):
        self.tokens = tokens
        self.player_service = player_service
        self.reconnect_lock = Lock()

    async def create_reconnect_token(self, player_id: str) -> str:
        async with self.reconnect_lock:
            old = await self.tokens.get_token_for_player(player_id)
            if old:
                await self.tokens.remove(old)

            token = secrets.token_hex(16)
            expires_at = None
            # expires_at = datetime.now(timezone.utc) + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

            await self.tokens.add(token, ReconnectToken(player_id=player_id, expires_at=expires_at))

            return token

    async def _consume_reconnect_token(self, token: str, now: datetime) -> str:
        async with self.reconnect_lock:
            entry = await self.tokens.remove(token)

            if not entry:
                raise InvalidReconnectToken()

            if entry.expires_at and entry.expires_at < now:
                raise InvalidReconnectToken()

            return entry.player_id

    async def disconnect(self, player_id) -> None:
        async with self.reconnect_lock:
            player = await self.player_service.get_player(player_id)
            player.is_connected = False
            token = await self.tokens.get_token_for_player(player_id)
            entry = await self.tokens.get(token) if token else None
            if not token or not entry:
                raise InvalidReconnectToken()

            entry.expires_at = datetime.now(timezone.utc) + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)
            await self.tokens.add(token, entry)

    async def handle_reconnect(self, reconnection_token: str, now: datetime) -> Player:
        player_id = await self._consume_reconnect_token(reconnection_token, now)

        player = await self.player_service.get_player(player_id)
        player.is_connected = True

        return player

    async def cleanup_expired_tokens(self):
        now = datetime.now(timezone.utc)

        async with self.reconnect_lock:
            for token, entry in await self.tokens.list():
                if entry.expires_at and entry.expires_at < now:
                    await self.tokens.remove(token)
