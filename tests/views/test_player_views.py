class TestPlayerViews:
    url = "/api/player"

    async def test_get_player_profile(self, client_with_no_db, test_player):
        response = client_with_no_db.get(f"{self.url}/{test_player.id}/profile")

        assert response.status_code == 200
        assert response.json()["username"]

    async def test_get_player_info__user_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/abc")

        assert response.status_code == 404
