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
