import secrets
from asyncio import Lock
from datetime import datetime, timedelta, timezone

from app.exceptions import InvalidReconnectToken
from app.game.dataclasses import Player, ReconnectToken
from app.services.player_service import PlayerService
from app.services.room_service import RoomService

RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


class ReconnectService:
    reconnect_tokens: dict[str, ReconnectToken] = {}  # token -> ReconnectToken(player_id, expires_at)
    player_tokens: dict[str, str] = {}  # player_id -> token
    reconnect_lock: Lock = Lock()

    def __init__(self, room_service: RoomService, player_service: PlayerService):
        self.room_service = room_service
        self.player_service = player_service

    async def create_reconnect_token(self, player_id: str) -> str:
        async with self.reconnect_lock:
            old = self.player_tokens.pop(player_id, None)
            if old:
                self.reconnect_tokens.pop(old, None)

            token = secrets.token_hex(16)
            expires_at = None
            # expires_at = datetime.now(timezone.utc) + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

            self.player_tokens[player_id] = token
            self.reconnect_tokens[token] = ReconnectToken(player_id=player_id, expires_at=expires_at)

            return token

    async def _consume_reconnect_token(self, token: str, now: datetime) -> str:
        async with self.reconnect_lock:
            entry = self.reconnect_tokens.pop(token, None)

            if not entry:
                raise InvalidReconnectToken()

            if entry.expires_at and entry.expires_at < now:
                self.player_tokens.pop(entry.player_id, None)
                raise InvalidReconnectToken()

            self.player_tokens.pop(entry.player_id, None)
            return entry.player_id

    async def disconnect(self, player_id) -> None:
        async with self.reconnect_lock:
            player = self.player_service.get_player(player_id)
            player.is_connected = False
            token = self.player_tokens.get(player_id, None)
            if not token:
                raise InvalidReconnectToken()

            self.reconnect_tokens[token].expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=RECONNECT_TOKEN_TTL_SECONDS
            )

    async def handle_reconnect(self, reconnection_token: str, now: datetime) -> Player:
        player_id = await self._consume_reconnect_token(reconnection_token, now)

        player = self.player_service.get_player(player_id)
        player.is_connected = True

        return player

    async def cleanup_expired_tokens(self):
        now = datetime.now(timezone.utc)

        async with self.reconnect_lock:
            for token, entry in list(self.reconnect_tokens.items()):
                if entry.expires_at < now:
                    self.reconnect_tokens.pop(token, None)
                    self.player_tokens.pop(entry.player_id, None)
