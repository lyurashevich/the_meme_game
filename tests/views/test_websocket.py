from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from starlette.websockets import WebSocketDisconnect

from app.websockets.views import websocket_endpoint
from tests.helpers import events_for, last_room_state


class TestWebsocket:
    def test_new_connection_creates_player(self, client_with_no_db):
        with client_with_no_db.websocket_connect("/ws") as ws:
            session = ws.receive_json()
            rooms_list = ws.receive_json()

        assert session["event"] == "session"
        assert session["payload"]["player_id"]
        assert session["payload"]["reconnect_token"]
        assert rooms_list == {"event": "rooms_list", "payload": []}

    def test_reconnect_restores_player_and_room(self, client_with_no_db):
        with client_with_no_db.websocket_connect("/ws") as ws:
            session = ws.receive_json()["payload"]
            ws.receive_json()  # rooms_list
            ws.send_json({"event": "create_room", "request_id": "c", "payload": {}})
            room_id = ws.receive_json()["payload"]["room"]["id"]  # room_state

        with client_with_no_db.websocket_connect(f"/ws?reconnect_token={session['reconnect_token']}") as ws:
            new_session = ws.receive_json()
            room_state = ws.receive_json()

        assert new_session["payload"]["player_id"] == session["player_id"]
        assert new_session["payload"]["reconnect_token"] != session["reconnect_token"]  # tokens are single-use
        assert room_state["event"] == "room_state"
        assert room_state["payload"]["room"]["id"] == room_id
        assert room_state["payload"]["chat"] == []

    async def test_expired_token_creates_new_player(self, client_with_no_db, reconnect_service):
        with client_with_no_db.websocket_connect("/ws") as ws:
            session = ws.receive_json()["payload"]

        token = session["reconnect_token"]
        entry = await reconnect_service.tokens.get(token)
        entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        with client_with_no_db.websocket_connect(f"/ws?reconnect_token={token}") as ws:
            new_session = ws.receive_json()["payload"]

        assert new_session["player_id"] != session["player_id"]


class TestWebsocketDisconnect:
    """Calls websocket_endpoint directly with a mocked WebSocket instead of going through
    TestClient.websocket_connect - the `client` fixture used by TestWebsocket above is an
    httpx.AsyncClient, which doesn't support websocket_connect at all (see the xfail tests)."""

    async def test_websocket_disconnect_notifies_other_players_in_room(
        self, websocket, services, player_service, room_service, outbox
    ):
        leaving_player = await player_service.create_player()
        other_player = await player_service.create_player()
        room = await room_service.create_room(owner=leaving_player)
        await room_service.join_room(room.id, other_player)

        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

        with patch.object(player_service, "create_player", new_callable=AsyncMock, return_value=leaving_player):
            await websocket_endpoint(websocket=websocket, reconnect_token=None, services=services)

        assert leaving_player.is_connected is False
        players = {p["id"]: p for p in last_room_state(outbox, other_player.id)["players"]}
        assert players[leaving_player.id]["is_connected"] is False
        assert players[other_player.id]["is_connected"] is True

    async def test_websocket_without_room_gets_session_and_rooms_list(self, websocket, services, outbox):
        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

        await websocket_endpoint(websocket=websocket, reconnect_token=None, services=services)

        assert [message["event"] for _, message in outbox] == ["session", "rooms_list"]

    async def test_websocket_with_removed_room_gets_rooms_list(
        self, websocket, services, player_service, room_service, outbox
    ):
        player = await player_service.create_player()
        room = await room_service.create_room(owner=player)
        await room_service.cleanup_room(room.id)  # player.room_id is now a dangling reference

        websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

        with patch.object(player_service, "create_player", new_callable=AsyncMock, return_value=player):
            await websocket_endpoint(websocket=websocket, reconnect_token=None, services=services)

        assert player.room_id is None
        assert [message["event"] for message in events_for(outbox, player.id)] == ["session", "rooms_list"]
