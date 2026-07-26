class TestGameViews:

    def setup_method(self):
        self.url = "/game"

    async def test_start_game(self, client_with_no_db, test_player, test_room_with_players, game_manager):
        response = client_with_no_db.post(f"{self.url}/start", json={"room_id": test_room_with_players.id})
        game_data = response.json()

        expected_json = {
            "id": game_data["id"],
            "room_id": game_data["room_id"],
            "leader_index": game_data["leader_index"],
            "players": game_data["players"],
            "meme_deck_count": game_data["meme_deck_count"],
            "situation_deck_count": game_data["situation_deck_count"],
        }

        assert response.status_code == 201
        assert response.json() == expected_json

    async def test_game_settings(self, client_with_no_db, prepared_game, override_game_service):
        data = {"max_rounds": 10, "round_time_limit": 60, "score_to_win": None}
        response = client_with_no_db.put(f"{self.url}/{prepared_game.room_id}/game_settings", json=data)

        assert response.status_code == 200
        assert prepared_game.settings.round_time_limit == 60
        assert prepared_game.settings.max_rounds == 10
        assert prepared_game.settings.score_to_win is None
        assert response.json() == data

    async def test_game_settings__wrong_value(self, client_with_no_db, prepared_game, override_game_service):
        response = client_with_no_db.put(
            f"{self.url}/{prepared_game.room_id}/game_settings",
            json={"max_rounds": -10, "round_time_limit": 60, "score_to_win": None},
        )

        assert response.status_code == 422
        assert prepared_game.settings.max_rounds is None

    async def test_game_settings__game_not_found(self, client_with_no_db):
        response = client_with_no_db.put(
            f"{self.url}/12344/game_settings", json={"max_rounds": 3, "round_time_limit": 60, "score_to_win": None}
        )

        assert response.status_code == 404
