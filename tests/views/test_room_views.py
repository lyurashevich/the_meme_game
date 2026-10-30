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

    async def test_rounds_count_is_the_rounds_limit(self, client_with_no_db, test_room):
        """Before: roundsCount returned the turn time (60) instead of the number of rounds."""
        response = client_with_no_db.get(f"{self.url}/{test_room.id}")
        assert response.json()["roundsCount"] is None  # no limit by default
        assert response.json()["timeLimit"] == 60

        test_room.settings.max_rounds = 5

        response = client_with_no_db.get(f"{self.url}/{test_room.id}")
        assert response.json()["roundsCount"] == 5
        assert response.json()["timeLimit"] == 60
