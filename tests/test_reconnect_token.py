from datetime import datetime, timedelta, timezone

import pytest

from app.exceptions import InvalidReconnectToken
from app.services.reconnect_service import RECONNECT_TOKEN_TTL_SECONDS


class TestReconnectTokens:
    async def test_create_token(self, player_service, reconnect_service):
        player = await player_service.create_player()
        token = await reconnect_service.create_reconnect_token(player.id)

        entry = await reconnect_service.tokens.get(token)
        assert entry
        assert entry.player_id == player.id
        assert not entry.expires_at

    async def test_successful_consume(self, player_service, reconnect_service):
        player = await player_service.create_player()
        now = datetime.now(timezone.utc)
        token = await reconnect_service.create_reconnect_token(player.id)
        (await reconnect_service.tokens.get(token)).expires_at = now + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # consume within TTL
        player_id = await reconnect_service._consume_reconnect_token(token, now + timedelta(seconds=30))
        assert player_id == player.id
        assert await reconnect_service.tokens.get(token) is None

    async def test_expired_token(self, player_service, reconnect_service):
        player = await player_service.create_player()
        # create token as if created RECONNECT_TOKEN_TTL_SECONDS+1 seconds ago -> expired
        created_at = datetime.now(timezone.utc) - timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS + 1)
        token = await reconnect_service.create_reconnect_token(player.id)
        (await reconnect_service.tokens.get(token)).expires_at = created_at

        with pytest.raises(InvalidReconnectToken):
            await reconnect_service._consume_reconnect_token(token, datetime.now(timezone.utc))

        # expired token should be removed
        assert await reconnect_service.tokens.get(token) is None

    async def test_cleanup_expired_tokens(self, player_service, reconnect_service):
        player_valid = await player_service.create_player()
        player_expired = await player_service.create_player()

        now = datetime.now(timezone.utc)
        token_valid = await reconnect_service.create_reconnect_token(player_valid.id)
        (await reconnect_service.tokens.get(token_valid)).expires_at = now + timedelta(seconds=40)
        token_expired = await reconnect_service.create_reconnect_token(player_expired.id)
        (await reconnect_service.tokens.get(token_expired)).expires_at = now - timedelta(
            seconds=RECONNECT_TOKEN_TTL_SECONDS + 1
        )

        # cleanup should remove expired and keep valid
        await reconnect_service.cleanup_expired_tokens()
        assert await reconnect_service.tokens.get(token_valid) is not None
        assert await reconnect_service.tokens.get(token_expired) is None

    async def test_token_removed_after_consume(self, player_service, reconnect_service):
        player = await player_service.create_player()
        now = datetime.now(timezone.utc)
        token = await reconnect_service.create_reconnect_token(player.id)
        (await reconnect_service.tokens.get(token)).expires_at = now + timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # consume and ensure removed
        _ = await reconnect_service._consume_reconnect_token(token, now + timedelta(seconds=1))
        assert await reconnect_service.tokens.get(token) is None
        # player's attribute should also be cleared after consume
        await player_service.get_player(player.id)

    async def test_consume_token_when_player_missing(self, game_manager, player_service, reconnect_service):
        # create player and token, then remove player before consuming
        player = await player_service.create_player()
        now = datetime.now(timezone.utc)
        token = await reconnect_service.create_reconnect_token(player.id)
        (await reconnect_service.tokens.get(token)).expires_at = now - timedelta(seconds=RECONNECT_TOKEN_TTL_SECONDS)

        # simulate player removed (race scenario)
        await player_service.players.remove(player.id)

        # consuming should raise InvalidReconnectToken and token should be removed
        with pytest.raises(InvalidReconnectToken):
            # Consume at a valid time (within TTL, not expired)
            await reconnect_service._consume_reconnect_token(token, now + timedelta(seconds=30))

        assert await reconnect_service.tokens.get(token) is None
