class TestGameViews:

    def setup_method(self):
        self.url = "/api/game"

    async def test_get_game_settings(self, client_with_no_db, test_room):
        response = client_with_no_db.get(f"{self.url}/{test_room.id}/game_settings")

        assert response.status_code == 200
        assert response.json() == {"round_time_limit": 60, "max_rounds": None, "score_to_win": None}

    async def test_get_game_settings__room_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/12344/game_settings")

        assert response.status_code == 404

    async def test_get_game_score(self, client_with_no_db, prepared_game):
        prepared_game.room.players[1].score = 2

        response = client_with_no_db.get(f"{self.url}/{prepared_game.room_id}/score")

        assert response.status_code == 200
        scores = {entry["id"]: entry["score"] for entry in response.json()}
        assert scores == {player.id: player.score for player in prepared_game.room.players}

    async def test_get_game_score__game_not_found(self, client_with_no_db):
        response = client_with_no_db.get(f"{self.url}/12344/score")

        assert response.status_code == 404
