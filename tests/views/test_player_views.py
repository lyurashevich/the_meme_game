import pytest


class TestPlayerViews:
    url = "/api/player"

    @pytest.mark.parametrize("username", ["q", "Matthew David McConaughey", "111111111"])
    def test_create_user(self, client_with_no_db, username):
        response = client_with_no_db.post(self.url, json={"username": username})

        assert response.status_code == 201
        assert response.json()["username"] == username

    def test_create_user__no_username(self, client_with_no_db):
        response = client_with_no_db.post(self.url, json={})

        assert response.status_code == 201
        assert response.json()["username"]

    async def test_get_player_profile(self, client_with_no_db, test_player):
        response = client_with_no_db.get(f"{self.url}/{test_player.id}/profile")

        assert response.status_code == 200
        assert response.json()["username"]

    async def test_get_player_info__user_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/abc")

        assert response.status_code == 404

    async def test_update_user(self, client_with_no_db, test_player):
        old_username = test_player.username

        response = client_with_no_db.patch(f"{self.url}/{test_player.id}/profile", json={"username": "new_username"})

        assert response.status_code == 200
        assert old_username != test_player.username
        assert test_player.username == "new_username"
