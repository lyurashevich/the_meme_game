from app.game.game import game_logic
from app.game.game_manager import get_game_manager
from tests.conftest import prepared_game


class TestRoundViews:
    def setup_method(self):
        self.url = "/round"
        self.manager = get_game_manager()

    def test_start_first_round(self, client_with_no_db, prepared_game):
        response = client_with_no_db.post(f"{self.url}/{prepared_game.room.id}/start")

        expected_json = {
            "game_id": prepared_game.id,
            "round_number": prepared_game.current_round.round_number,
            "leader_id": prepared_game.current_round.leader_id,
            "situation_card_text": prepared_game.current_round.situation_card_text,
            "time_limit": prepared_game.current_round.time_limit,
        }

        assert response.status_code == 201
        assert response.json() == expected_json

    async def test_get_game_round_info(self, client_with_no_db, prepared_game):
        await game_logic.start_first_round(prepared_game)

        response = client_with_no_db.get(f"{self.url}/{prepared_game.room_id}/current")

        expected_json = {
            "game_id": prepared_game.id,
            "round_number": prepared_game.current_round.round_number,
            "leader_id": prepared_game.current_round.leader_id,
            "situation_card_id": prepared_game.current_round.situation_card_id,
            "player_choices_list": list(prepared_game.current_round.player_choices),
            "time_limit": prepared_game.current_round.time_limit,
        }

        assert response.status_code == 200
        assert response.json() == expected_json
