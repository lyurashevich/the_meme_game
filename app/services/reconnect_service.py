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
from app.services.player_service import PlayerService
from app.services.room_service import RoomService

RECONNECT_TOKEN_TTL_SECONDS = 60  # TTL for reconnect token (seconds)


class ReconnectService:
    reconnect_tokens: dict[str, ReconnectToken] = {}  # token -> ReconnectToken(player_id, expires_at)
    player_tokens: dict[str, str] = {}  # player_id -> token
    reconnect_lock: Lock = Lock()

    def __init__(self, room_service: RoomService, player_service: PlayerService, game_manager: GameManager):
        self.room_service = room_service
        self.player_service = player_service
        self.game_manager = game_manager

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
                if entry.expires_at and entry.expires_at < now:
                    self.reconnect_tokens.pop(token, None)
                    self.player_tokens.pop(entry.player_id, None)

    async def build_reconnect_payload(self, player: Player, token: str) -> tuple[str, dict]:
        """Build the PLAYER_RECONNECTED payload. Assumes ``player.room_id`` is set —
        callers are expected to check this before calling (see websocket_endpoint)."""
        if not player.room_id:
            raise RoomNotFoundException()

        async with self.room_service.get_room_lock(room_id=player.room_id):
            room = self.room_service.get_room(player.room_id)
            payload_data: dict[str, Any] = {
                "reconnect_token": token,
                "room_id": player.room_id,
                "room_name": room.name,
                "avatar": player.avatar,
            }

            try:
                game = self.game_manager.get_game(player.room_id)
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
                        "handed_cards": [card.to_dict() for card in player.handed_cards],
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
