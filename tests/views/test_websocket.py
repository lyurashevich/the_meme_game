from datetime import datetime, timedelta, timezone

from app.game.game_manager import get_game_manager


class TestWebsocket:
    def test_websocket_creates_player(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()

            assert response["event"] == "player_created"

            assert "player_id" in response["payload"]
            assert response["payload"]["player_id"] is not None

            assert "reconnect_token" in response["payload"]
            assert response["payload"]["reconnect_token"] is not None

    def test_websocket_reconnect(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()

            reconnect_token = response["payload"]["reconnect_token"]

        with client.websocket_connect(f"/ws/?reconnect_token={reconnect_token}") as ws:
            reconnect_response = ws.receive_json()
            restore_state = ws.receive_json()
            room_state = ws.receive_json()

            assert restore_state["event"] == "restore_state"
            assert room_state["event"] == "room_state"
            assert reconnect_response["event"] == "player_reconnected"

    def test_websocket_reconnect_after_timeout(self, client):
        manager = get_game_manager()

        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()
            payload = response["payload"]
            reconnect_token = payload["reconnect_token"]

        player = manager.get_player_by_reconnect_token(reconnect_token)
        player.disconnected_at = datetime.now(timezone.utc) - timedelta(seconds=61)

        with client.websocket_connect(f"/ws/?reconnect_token={reconnect_token}") as ws:
            response = ws.receive_json()

            assert response["event"] == "reconnection_failed"
