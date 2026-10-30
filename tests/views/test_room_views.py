class TestRoomViews:

    def setup_method(self):
        self.url = "/api/room"

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
