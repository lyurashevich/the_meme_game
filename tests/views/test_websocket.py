from datetime import datetime, timedelta, timezone

import pytest

from app.dependencies import game_manager
from app.game.enums import WebsocketEvents


class TestWebsocket:
    def test_websocket_creates_player(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()

            assert response["event"] == "player_created"

            assert "player_id" in response["payload"]
            assert response["payload"]["player_id"] is not None

    @pytest.mark.skip
    def test_websocket_reconnect(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()

            player_id = response["payload"]["player_id"]

        reconnect_token = next(
            key for key, value in game_manager.reconnect_tokens.items() if value.player_id == player_id
        )

        with client.websocket_connect(f"/ws/?reconnect_token={reconnect_token}") as ws:
            reconnect_response = ws.receive_json()
            restore_state = ws.receive_json()

            assert restore_state["event"] == "restore_state"
            assert reconnect_response["event"] == WebsocketEvents.PLAYER_RECONNECTED.value

    def test_websocket_reconnect_after_timeout(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()
            payload = response["payload"]
            player_id = payload["player_id"]

        reconnect_token = next(
            key for key, value in game_manager.reconnect_tokens.items() if value.player_id == player_id
        )
        token = game_manager.reconnect_tokens.get(reconnect_token)
        token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=100)

        with client.websocket_connect(f"/ws/?reconnect_token={reconnect_token}") as ws:
            response = ws.receive_json()

            new_player_id = response["payload"]["player_id"]
            assert response["event"] == "player_created"
            assert player_id != new_player_id
