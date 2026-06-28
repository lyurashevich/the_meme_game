from unittest.mock import AsyncMock

from app.dependencies import connection_manager, game_manager, get_websocket_sender
from app.game.enums import WebsocketEvents
from app.main import app


class TestRoomViews:

    def setup_method(self):
        self.url = "/room"

    async def test_create_room(self, client_with_no_db, test_player):

        response = client_with_no_db.post(self.url, json={"player_id": test_player.id})

        assert response.status_code == 201
        assert response.json()["owner_id"] == test_player.id
        assert response.json()["players_count"] == 1
        assert response.json()["name"].startswith("room")

    async def test_create_room__no_player_id(self, client_with_no_db):

        response = client_with_no_db.post(self.url, json={})

        assert response.status_code == 422

    async def test_create_room__player_not_found(self, client_with_no_db):
        response = client_with_no_db.post(self.url, json={"player_id": "abc"})

        assert response.status_code == 404

    async def test_get_room(self, client_with_no_db, test_room):
        response = client_with_no_db.get(f"{self.url}/{test_room.id}")

        assert response.status_code == 200
        assert response.json()["name"].startswith("room")
        assert response.json()["players_count"] == 1

    async def test_get_room__room_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/abc")

        assert response.status_code == 404

    async def test_get_rooms(self, client_with_no_db, test_player):
        room = await game_manager.create_room(owner=test_player)
        response = client_with_no_db.get(f"{self.url}/all")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == room.name

    async def test_join_room(self, test_room, test_player, client_with_no_db):
        sender_mock = AsyncMock()
        sender_mock.send = AsyncMock()
        app.dependency_overrides[get_websocket_sender] = lambda: sender_mock

        new_player = await game_manager.create_player()

        response = client_with_no_db.patch(f"{self.url}/{test_room.id}", json={"player_id": new_player.id})

        assert response.status_code == 200

        updated_room = game_manager.active_rooms.get(test_room.id)
        assert new_player in game_manager.players.values()
        assert new_player in updated_room.players
        sender_mock.send.assert_called_once_with(
            player_id=new_player.id,
            event=WebsocketEvents.PLAYER_JOINED_ROOM.value,
            payload={"room_id": test_room.id},
        )

    async def test_leave_room(self, websocket, test_room, client_with_no_db):
        new_player = await game_manager.create_player()
        await game_manager.join_room(test_room.id, new_player, connection_manager)

        response = client_with_no_db.patch(f"{self.url}/{test_room.id}/leave", json={"player_id": new_player.id})

        assert response.status_code == 200

        updated_room = game_manager.active_rooms.get(test_room.id)
        assert new_player in game_manager.players.values()
        assert new_player not in updated_room.players
