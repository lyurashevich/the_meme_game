import secrets
from asyncio import Lock
from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import (
    GameNotFoundException,
    InvalidReconnectToken,
    RoomNotFoundException,
)
from app.game.dataclasses import Player, ReconnectToken
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.repositories.base import ReconnectTokenRepository
from app.services.player_service import PlayerService
from app.services.room_service import RoomService

RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


class ReconnectService:
    def __init__(
        self,
        tokens: ReconnectTokenRepository,
        room_service: RoomService,
        player_service: PlayerService,
        game_manager: GameManager,
    ):
        self.tokens = tokens
        self.room_service = room_service
        self.player_service = player_service
        self.game_manager = game_manager
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

    async def build_reconnect_payload(self, player: Player, token: str) -> tuple[str, dict]:
        """Build the PLAYER_RECONNECTED payload. Assumes ``player.room_id`` is set —
        callers are expected to check this before calling (see websocket_endpoint)."""
        if not player.room_id:
            raise RoomNotFoundException()

        async with self.room_service.get_room_lock(room_id=player.room_id):
            room = await self.room_service.get_room(player.room_id)
            payload_data: dict[str, Any] = {
                "reconnect_token": token,
                "room_id": player.room_id,
                "room_name": room.name,
                "avatar_id": player.avatar_id,
            }

            try:
                game = await self.game_manager.get_game(player.room_id)
            except GameNotFoundException:
                game = None

            if game:
                payload_data.update(
                    {
                        "players_choice": (
                            [
                                {"player_id": player_id, "card": card.to_dict()}
                                for player_id, card in game.current_round.player_choices.items()
                            ]
                            if game.current_round
                            else []
                        ),
                        "hand_cards": [card.to_dict() for card in player.hand_cards],
                        "score": player.score,
                        "is_host": player.is_host,
                        "players": (
                            [
                                {
                                    "id": player.id,
                                    "username": player.username,
                                    "is_connected": player.is_connected,
                                    "score": player.score,
                                }
                                for player in room.players
                            ]
                            if room
                            else []
                        ),
                        "game_state": game.state.value if game else None,
                        "round_state": (game.current_round.state.value if game and game.current_round else None),
                        "current_round_number": (game.current_round.round_number if game.current_round else None),
                        "leader_id": (game.current_round.leader_id if game.current_round else None),
                        "current_situation_card": (
                            game.current_round.situation_card.to_dict() if game.current_round else None
                        ),
                    }
                )

            data = {"event": WebsocketEvents.PLAYER_RECONNECTED.value, "payload": payload_data}

            return player.id, data
