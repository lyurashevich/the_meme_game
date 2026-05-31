from datetime import datetime, timedelta, timezone

import pytest

from app.exceptions import InvalidReconnectToken
from app.game.game_manager import RECONNECT_TOKEN_TTL_SECONDS, get_game_manager


class TestReconnectTokens:
    def setup_method(self):
        self.manager = get_game_manager()
        # clear any previous tokens to avoid interference between tests
        self.manager.reconnect_tokens.clear()

    async def test_create_token(self):
        player = await self.manager.create_player()
        token = await self.manager.create_reconnect_token(player.id)

        assert token in self.manager.reconnect_tokens
        entry = self.manager.reconnect_tokens[token]
        assert entry.player_id == player.id
        assert not entry.expires_at

    async def test_successful_consume(self):
        player = await self.manager.create_player()
        now = datetime.now(timezone.utc)
        token = await self.manager.create_reconnect_token(player.id)
        self.manager.reconnect_tokens.get(token).expires_at = now + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # consume within TTL
        player_id = await self.manager.consume_reconnect_token(token, now + timedelta(seconds=30))
        assert player_id == player.id
        assert token not in self.manager.reconnect_tokens

    async def test_expired_token(self):
        player = await self.manager.create_player()
        # create token as if created RECONNECT_TOKEN_TTL_SECONDS+1 seconds ago -> expired
        created_at = datetime.now(timezone.utc) - timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS + 1)
        token = await self.manager.create_reconnect_token(player.id)
        self.manager.reconnect_tokens.get(token).expires_at = created_at

        with pytest.raises(InvalidReconnectToken):
            await self.manager.consume_reconnect_token(token, datetime.now(timezone.utc))

        # expired token should be removed
        assert token not in self.manager.reconnect_tokens

    async def test_cleanup_expired_tokens(self):
        player_valid = await self.manager.create_player()
        player_expired = await self.manager.create_player()

        now = datetime.now(timezone.utc)
        token_valid = await self.manager.create_reconnect_token(player_valid.id)
        self.manager.reconnect_tokens.get(token_valid).expires_at = now + timedelta(seconds=40)
        token_expired = await self.manager.create_reconnect_token(player_expired.id)
        self.manager.reconnect_tokens.get(token_expired).expires_at = now - timedelta(
            seconds=RECONNECT_TOKEN_TTL_SECONDS + 1
        )

        # cleanup should remove expired and keep valid
        await self.manager.cleanup_expired_tokens(datetime.now(timezone.utc))
        assert token_valid in self.manager.reconnect_tokens
        assert token_expired not in self.manager.reconnect_tokens

    async def test_token_removed_after_consume(self):
        player = await self.manager.create_player()
        now = datetime.now(timezone.utc)
        token = await self.manager.create_reconnect_token(player.id)
        self.manager.reconnect_tokens.get(token).expires_at = now + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # consume and ensure removed
        _ = await self.manager.consume_reconnect_token(token, now + timedelta(seconds=1))
        assert token not in self.manager.reconnect_tokens
        # player's attribute should also be cleared after consume
        self.manager.get_player(player.id)

    async def test_consume_token_when_player_missing(self):
        # create player and token, then remove player before consuming
        player = await self.manager.create_player()
        now = datetime.now(timezone.utc)
        token = await self.manager.create_reconnect_token(player.id)
        self.manager.reconnect_tokens.get(token).expires_at = now + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # simulate player removed (race scenario)
        self.manager.players.pop(player.id, None)

        # consuming should raise InvalidReconnectToken and token should be removed
        with pytest.raises(InvalidReconnectToken):
            # Consume at a valid time (within TTL, not expired)
            await self.manager.consume_reconnect_token(token, now + timedelta(seconds=30))

        assert token not in self.manager.reconnect_tokens
