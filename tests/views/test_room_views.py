import pytest


class TestRoomViews:

    def setup_method(self):
        self.url = "/api/room"

    async def test_create_room(self, client_with_no_db, test_player):

        response = client_with_no_db.post(self.url, json={"player_id": test_player.id})

        assert response.status_code == 201
        assert response.json()["ownerId"] == test_player.id
        assert response.json()["playersCount"] == 1
        assert response.json()["name"]

    async def test_create_room__no_player_id(self, client_with_no_db):

        response = client_with_no_db.post(self.url, json={})

        assert response.status_code == 422

    async def test_create_room__player_not_found(self, client_with_no_db):
        response = client_with_no_db.post(self.url, json={"player_id": "abc"})

        assert response.status_code == 404

    async def test_get_room(self, client_with_no_db, test_room):
        response = client_with_no_db.get(f"{self.url}/{test_room.id}")

        assert response.status_code == 200
        assert response.json()["name"]
        assert response.json()["playersCount"] == 1

    async def test_get_room__room_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/abc")

        assert response.status_code == 404

    async def test_get_rooms(self, client_with_no_db, test_player, room_service):
        room = await room_service.create_room(owner=test_player)
        response = client_with_no_db.get(f"{self.url}/all")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == room.name

    async def test_join_room(self, test_room, test_player, client_with_no_db, player_service, room_service):

        new_player = player_service.create_player()

        response = client_with_no_db.patch(
            f"{self.url}/{test_room.id}", json={"player_id": new_player.id, "room_id": test_room.id}
        )

        assert response.status_code == 200

        updated_room = room_service.active_rooms.get(test_room.id)
        assert new_player in player_service.players.values()
        assert new_player in updated_room.players

    @pytest.mark.xfail
    async def test_leave_room(self, websocket, test_room, client_with_no_db, player_service, room_service):
        new_player = player_service.create_player()
        await room_service.join_room(test_room.id, new_player)

        response = client_with_no_db.patch(
            f"{self.url}/{test_room.id}/leave", json={"player_id": new_player.id, "room_id": test_room.id}
        )

        assert response.status_code == 200

        updated_room = room_service.active_rooms.get(test_room.id)
        assert new_player in player_service.players.values()
        assert new_player not in updated_room.players
