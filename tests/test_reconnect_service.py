from app.game.enums import WebsocketEvents


class TestBuildReconnectPayload:
    async def test_without_active_game(self, test_room, test_player, reconnect_service):
        recipient_id, message = await reconnect_service.build_reconnect_payload(test_player, "token-123")

        assert recipient_id == test_player.id
        assert message == {
            "event": WebsocketEvents.PLAYER_RECONNECTED.value,
            "payload": {
                "reconnect_token": "token-123",
                "room_id": test_room.id,
                "room_name": test_room.name,
                "avatar": test_player.avatar,
            },
        }

    async def test_with_game_but_no_round_started_yet(self, prepared_game, test_player, reconnect_service):
        recipient_id, message = await reconnect_service.build_reconnect_payload(test_player, "token-789")

        assert recipient_id == test_player.id
        payload = message["payload"]
        assert payload["game_state"] == prepared_game.state.value
        assert payload["round_state"] is None
        assert payload["current_round_number"] is None
        assert payload["leader_id"] is None
        assert payload["current_situation_card"] is None
        assert payload["players_choice"] == []

    async def test_with_active_game(self, prepared_game, game_service, test_player, reconnect_service):
        await game_service.start_first_round(prepared_game.room_id)
        current_round = prepared_game.current_round

        recipient_id, message = await reconnect_service.build_reconnect_payload(test_player, "token-456")

        assert recipient_id == test_player.id
        payload = message["payload"]
        assert payload["reconnect_token"] == "token-456"
        assert payload["game_state"] == prepared_game.state.value
        assert payload["round_state"] == current_round.state.value
        assert payload["current_round_number"] == current_round.round_number
        assert payload["leader_id"] == test_player.id
        assert payload["players_choice"] == []
        assert payload["handed_cards"] == [card.to_dict() for card in test_player.handed_cards]
        assert payload["is_host"] == test_player.is_host
        assert {p["id"] for p in payload["players"]} == {p.id for p in prepared_game.room.players}
