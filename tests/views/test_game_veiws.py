from app.game.game_manager import get_game_manager


class TestGameViews:

    def setup_method(self):
        self.manager = get_game_manager()
        self.url = "/game"

    async def test_start_game(self, client_with_no_db, test_player, test_room_with_players):
        response = client_with_no_db.post(f"{self.url}/start", json={"room_id": test_room_with_players.id})

        game = self.manager.get_game(room_id=test_room_with_players.id)

        expected_json = {
            "id": game.id,
            "room_id": test_room_with_players.id,
            "leader_index": game.leader_index,
            "players": [player.id for player in test_room_with_players.players],
            "meme_deck_count": len(game.meme_deck),
            "situation_deck_count": len(game.situation_deck),
        }

        assert response.status_code == 201
        assert response.json() == expected_json
