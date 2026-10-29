from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.game.enums import WebsocketEvents
from app.websockets.views import websocket_endpoint


class TestWebsocket:
    @pytest.mark.xfail
    def test_websocket_creates_player(self, client):
        with client.websocket_connect("/ws/") as ws:
            response = ws.receive_json()

            assert response["event"] == "player_created"

            assert "player_id" in response["payload"]
            assert response["payload"]["player_id"] is not None

    @pytest.mark.xfail
    def test_websocket_reconnect(self, client, game_manager):
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

    @pytest.mark.xfail
    def test_websocket_reconnect_after_timeout(self, client, game_manager):
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


class TestWebsocketDisconnect:
    """Calls websocket_endpoint directly with a mocked WebSocket instead of going through
    TestClient.websocket_connect - the `client` fixture used by TestWebsocket above is an
    httpx.AsyncClient, which doesn't support websocket_connect at all (see the xfail tests)."""

    async def test_websocket_disconnect_notifies_other_players_in_room(
        self, websocket, connection_manager, player_service, reconnect_service, room_service
    ):
        leaving_player = await player_service.create_player()
        other_player = await player_service.create_player()
        room = await room_service.create_room(owner=leaving_player)
        await room_service.join_room(room.id, other_player)

        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
        connection_manager.broadcast_to_players = AsyncMock()

        with patch.object(player_service, "create_player", new_callable=AsyncMock, return_value=leaving_player):
            await websocket_endpoint(
                websocket=websocket,
                reconnect_token=None,
                connection_manager=connection_manager,
                player_service=player_service,
                reconnect_service=reconnect_service,
                room_service=room_service,
            )

        disconnect_calls = [
            call
            for call in connection_manager.broadcast_to_players.await_args_list
            if call.args[1]["event"] == WebsocketEvents.PLAYER_DISCONNECTED.value
        ]
        assert len(disconnect_calls) == 1
        recipients, payload = disconnect_calls[0].args
        assert set(recipients) == {leaving_player.id, other_player.id}
        assert disconnect_calls[0].kwargs["exclude_id"] == leaving_player.id
        assert payload["payload"]["player_id"] == leaving_player.id
        assert leaving_player.is_connected is False

    async def test_websocket_disconnect_without_room_is_a_no_op(
        self, websocket, connection_manager, player_service, reconnect_service, room_service
    ):
        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
        connection_manager.broadcast_to_players = AsyncMock()

        await websocket_endpoint(
            websocket=websocket,
            reconnect_token=None,
            connection_manager=connection_manager,
            player_service=player_service,
            reconnect_service=reconnect_service,
            room_service=room_service,
        )

        connection_manager.broadcast_to_players.assert_not_awaited()

    async def test_websocket_disconnect_after_room_cleanup_is_a_no_op(
        self, websocket, connection_manager, player_service, reconnect_service, room_service
    ):
        player = await player_service.create_player()
        room = await room_service.create_room(owner=player)
        await room_service.cleanup_room(room.id)  # player.room_id is now a dangling reference

        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
        connection_manager.broadcast_to_players = AsyncMock()

        with patch.object(player_service, "create_player", new_callable=AsyncMock, return_value=player):
            await websocket_endpoint(
                websocket=websocket,
                reconnect_token=None,
                connection_manager=connection_manager,
                player_service=player_service,
                reconnect_service=reconnect_service,
                room_service=room_service,
            )

        connection_manager.broadcast_to_players.assert_not_awaited()
