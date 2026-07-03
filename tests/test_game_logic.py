from unittest.mock import patch

import pytest

from app.exceptions import (
    CardNotFoundException,
    GameNotFoundException,
    InvalidGameStateException,
    InvalidPlayerActionException,
    InvalidRoundStateException,
    NotEnoughCardsException,
    NotEnoughPlayersException,
    PlayerNotFoundException,
    RoomNotFoundException,
    RoundNotFoundException,
)
from app.game.enums import GameState, RoundState
from app.game.game import CARDS_PER_PLAYER


class TestGameLogic:
    async def test_get_room(self, test_room, room_service):
        room = room_service.get_room(test_room.id)

        assert room
        assert room.id == test_room.id

    async def test_get_room__not_found(self, room_service):
        with pytest.raises(RoomNotFoundException) as e:
            room_service.get_room("qwerty")

        assert str(e.value.message) == "Room not found"

    async def test_prepare_game(
        self, test_room_with_players, mock_situation_cards, mock_meme_cards, game_service, game_manager
    ):

        with patch("app.game.game.MemeService.get_meme_cards", return_value=mock_meme_cards), patch(
            "app.game.game.SituationService.get_situation_cards", return_value=mock_situation_cards
        ):

            game = await game_service.prepare_game(test_room_with_players.id)

        assert not game.current_round
        assert game.meme_deck_count == len(mock_meme_cards)
        assert game.situation_deck_count == len(mock_situation_cards)
        assert not game.meme_discard_pile
        assert not game.situation_discard_pile
        assert game.state == GameState.STARTING
        assert game.room == test_room_with_players
        assert game_manager.active_games[test_room_with_players.id] == game

    async def test_prepare_game__not_enough_players(self, test_room, game_service):
        with pytest.raises(NotEnoughPlayersException) as e:
            await game_service.prepare_game(test_room.id)

        assert str(e.value.message) == NotEnoughPlayersException.message

    async def test_prepare_game__room_not_found(self, game_service):
        with pytest.raises(RoomNotFoundException) as e:
            await game_service.prepare_game("qwerty")

        assert str(e.value.message) == RoomNotFoundException.message

    async def test_start_first_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)

        assert prepared_game.current_round.round_number == 1
        assert prepared_game.current_round.situation_card not in prepared_game.situation_deck
        assert not prepared_game.current_round.winner
        assert prepared_game.leader_index == 0
        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.state == RoundState.CHOOSING_CARDS
        for player in prepared_game.room.players:
            assert len(player.handed_cards) == CARDS_PER_PLAYER

    async def test_start_first_round__wrong_game_state(self, prepared_game, game_service):
        prepared_game.state = GameState.FINISHED
        with pytest.raises(InvalidGameStateException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.STARTING.value} to perform this action"
        )  # todo: подправить

    async def test_start_first_round__no_situation_cards(self, prepared_game, game_service):
        prepared_game.situation_deck.clear()
        with pytest.raises(NotEnoughCardsException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert str(e.value.message) == NotEnoughCardsException.message

    async def test_start_first_round__no_meme_cards(self, prepared_game, game_service):
        prepared_game.meme_deck.clear()
        with pytest.raises(NotEnoughCardsException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert str(e.value.message) == NotEnoughCardsException.message

    async def test_player_select_card(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert prepared_game.current_round.player_choices[player.id] == selected_card
        assert selected_card not in player.handed_cards
        assert len(player.handed_cards) == CARDS_PER_PLAYER - 1

    async def test_player_select_card__player_is_leader(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[0]
        selected_card = player.handed_cards[0]

        with pytest.raises(InvalidPlayerActionException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == "Invalid player action. Leader cannot choose a card"  # todo: подправить

    async def test_player_select_card__player_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)

        with pytest.raises(PlayerNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, "player.id", 999)

        assert str(e.value.message) == PlayerNotFoundException.message

    async def test_player_select_card__card_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]

        with pytest.raises(CardNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, 999)

        assert str(e.value.message) == CardNotFoundException.message

    async def test_player_select_card__wrong_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.state = GameState.FINISHED
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        with pytest.raises(InvalidGameStateException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_player_select_card__card_already_selected(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        prepared_game.current_round.player_choices[player.id] = player.handed_cards[0]
        selected_card = player.handed_cards[1]

        with pytest.raises(InvalidPlayerActionException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == "Invalid player action. Player already selected a card"  # todo: подправить

    async def test_player_select_card__round_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round = None
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        with pytest.raises(RoundNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_player_select_card__wrong_round_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        with pytest.raises(InvalidRoundStateException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert (
            str(e.value.message)
            == f"Invalid round state. Round state must be {RoundState.CHOOSING_CARDS.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        assert winner.score == 1

    async def test_leader_choose_winner__game_not_found(self, prepared_game, test_game, game_service):

        winner = prepared_game.room.players[2]

        with pytest.raises(GameNotFoundException) as e:
            await game_service.leader_choose_winner(test_game.room_id, winner.id)

        assert str(e.value.message) == GameNotFoundException.message

    async def test_leader_choose_winner__round_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round = None

        winner = prepared_game.room.players[2]

        with pytest.raises(RoundNotFoundException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, winner.id)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_leader_choose_winner__wrong_round_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner_id = prepared_game.room.players[2].id

        with pytest.raises(InvalidRoundStateException) as e:
            await game_service.leader_choose_winner(
                prepared_game.room_id, prepared_game.current_round.player_choices[winner_id].id
            )

        assert (
            str(e.value)
            == f"Invalid round state. Round state must be {RoundState.LEADER_CHOOSING.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner__wrong_game_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.state = GameState.FINISHED

        winner = prepared_game.room.players[2]

        with pytest.raises(InvalidGameStateException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, winner.id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner__player_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        with pytest.raises(PlayerNotFoundException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, "winner.id")

        assert str(e.value.message) == PlayerNotFoundException.message

    async def test_end_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner = prepared_game.room.players[2]
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(
            prepared_game.room_id, prepared_game.current_round.player_choices[winner.id].id
        )

        assert len(prepared_game.meme_discard_pile) > 0
        assert len(prepared_game.situation_discard_pile) > 0

    async def test_end_round__round_not_found(self, prepared_game, game_service):
        prepared_game.state = GameState.ACTIVE
        with pytest.raises(RoundNotFoundException) as e:
            await game_service.end_round(prepared_game.room_id)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_end_round__game_not_active(self, prepared_game, game_service):
        prepared_game.state = GameState.FINISHED
        with pytest.raises(InvalidGameStateException) as e:
            await game_service.end_round(prepared_game.room_id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_start_new_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(
            prepared_game.room_id, prepared_game.current_round.player_choices[prepared_game.room.players[2].id].id
        )

        assert prepared_game.current_round.round_number == 2
        assert prepared_game.leader_index == 1
        assert not prepared_game.current_round.winner
        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.state == RoundState.CHOOSING_CARDS
        assert len(prepared_game.meme_discard_pile) > 0
        assert len(prepared_game.meme_discard_pile) > 0
        assert prepared_game.current_round.situation_card not in prepared_game.situation_deck
        assert prepared_game.current_round.situation_card not in prepared_game.situation_discard_pile
        for player in prepared_game.room.players:
            assert len(player.handed_cards) == CARDS_PER_PLAYER
            assert len(set(player.handed_cards)) == CARDS_PER_PLAYER


# class TestCardCooldownSystem:
#     """Test card cooldown and availability system"""

#     # @pytest.mark.asyncio
#     async def test_get_available_meme_cards_no_cooldown(self, game_logic, game_with_cards):
#         """Test getting available meme cards with no cooldown"""
#         game_with_cards.round_number = 5
#         game_with_cards.meme_deck = [
#             MemeCard(id=1, image_url="test1.jpg", round_to_return=3),  # Available
#             MemeCard(id=2, image_url="test2.jpg", round_to_return=6),  # Not available
#             MemeCard(id=3, image_url="test3.jpg", round_to_return=None),  # Never used
#         ]

#         available = await game_logic.get_available_meme_cards(game_with_cards)

#         assert len(available) == 2
#         assert available[0].id == 1
#         assert available[1].id == 3

#     # @pytest.mark.asyncio
#     async def test_get_available_situation_cards_with_cooldown(self, game_logic, game_with_cards):
#         """Test getting available situation cards with cooldown"""
#         game_with_cards.round_number = 15
#         game_with_cards.situation_deck = [
#             SituationCard(id=1, text="Test 1", round_to_return=10),  # Available
#             SituationCard(id=2, text="Test 2", round_to_return=20),  # Not available
#             SituationCard(id=3, text="Test 3", round_to_return=None),  # Never used
#         ]

#         available = await game_logic.get_available_situation_cards(game_with_cards)

#         assert len(available) == 2
#         assert available[0].id == 1
#         assert available[1].id == 3


# class TestGameEndConditions:
#     """Test various game end conditions"""

#     # @pytest.mark.asyncio
#     @pytest.mark.parametrize("score_to_win,player_scores,should_end", [
#         (5, [5, 3, 2], True),
#         (5, [4, 3, 2], False),
#         (10, [8, 7, 6], False),
#         (None, [100, 50, 25], False),  # No score limit
#     ])
#     async def test_should_end_game_score_limit(
#       self, game_logic, game_with_cards, players, score_to_win, player_scores, should_end
#     ):
#         """Test game end based on score limit"""
#         game_logic.settings.score_to_win = score_to_win
#         game_with_cards.room.players = players[:3]

#         for i, player in enumerate(game_with_cards.room.players):
#             player.score = player_scores[i]

#         result = await game_logic.should_end_game(game_with_cards)
#         assert result == should_end

#     # @pytest.mark.asyncio
#     @pytest.mark.parametrize("max_rounds,current_round,should_end", [
#         (10, 10, True),
#         (10, 9, False),
#         (5, 3, False),
#         (None, 100, False),  # No round limit
#     ])
#     async def test_should_end_game_max_rounds(
#       self, game_logic, game_with_cards, max_rounds, current_round, should_end
#     ):
#         """Test game end based on max rounds"""
#         game_logic.settings.max_rounds = max_rounds
#         game_logic.settings.score_to_win = None  # Disable score limit
#         game_with_cards.round_number = current_round

#         result = await game_logic.should_end_game(game_with_cards)
#         assert result == should_end

#     # @pytest.mark.asyncio
#     async def test_should_end_game_no_situation_cards(self, game_logic, game_with_cards):
#         """Test game end when no situation cards available"""
#         game_logic.settings.score_to_win = None
#         game_logic.settings.max_rounds = None
#         game_with_cards.situation_deck = []  # No situation cards

#         result = await game_logic.should_end_game(game_with_cards)
#         assert result == True


# class TestEdgeCases:
#     """Test various edge cases and error conditions"""

#     # @pytest.mark.asyncio
#     async def test_hand_out_one_card_leader_excluded(self, game_logic, game_with_cards, players):
#         """Test that leader doesn't get a card when handing out one card"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.leader_index = 0
#         leader_initial_cards = len(players[0].handed_cards)

#         await game_logic.hand_out_one_card(game_with_cards)

#         # Leader should not get a new card
#         assert len(players[0].handed_cards) == leader_initial_cards
#         # Other players should get cards
#         for player in players[1:3]:
#             assert len(player.handed_cards) > 0

#     # @pytest.mark.asyncio
#     async def test_choose_leader_rotation(self, game_logic, game_with_cards, players):
#         """Test leader rotation through all players"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.leader_index = 0

#         # Test rotation
#         for i in range(3):
#             leader = await game_logic.choose_leader(game_with_cards)
#             expected_leader = players[(i + 1) % 3]
#             assert leader == expected_leader
#             assert game_with_cards.leader_index == (i + 1) % 3

#     # @pytest.mark.asyncio
#     async def test_end_card_selection_phase_all_players_chosen(self, game_logic, game_with_cards, players):
#         """Test automatic end of card selection when all players choose"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         # Simulate all non-leader players choosing cards
#         for player in players[1:3]:
#             game_with_cards.current_round.player_choices[player.id] = MemeCard(id=1, image_url="test.jpg")

#         # This should trigger automatic end of card selection
#         await game_logic.end_card_selection_phase(game_with_cards)

#         assert game_with_cards.current_round.state == RoundState.LEADER_CHOOSING
#         assert game_with_cards.state == GameState.ROUND_ENDING

#     # @pytest.mark.asyncio
#     async def test_cleanup_room_removes_all_data(self, game_logic, room, players):
#         """Test that room cleanup removes all associated data"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         game_logic.game_manager.active_games[room.id] = Game(room=room)
#         game_logic.game_manager.player_connections = {p.id: room.id for p in players}

#         await game_logic.cleanup_room(room.id)

#         assert room.id not in game_logic.game_manager.active_rooms
#         assert room.id not in game_logic.game_manager.active_games
#         assert all(room.id not in game_logic.game_manager.player_connections.values())

#     # @pytest.mark.asyncio
#     async def test_delayed_cleanup(self, game_logic, room):
#         """Test delayed cleanup functionality"""
#         game_logic.game_manager.active_rooms[room.id] = room

#         # Start delayed cleanup
#         task = asyncio.create_task(game_logic.delayed_cleanup(room.id, delay_seconds=0.1))

#         # Room should still exist immediately
#         assert room.id in game_logic.game_manager.active_rooms

#         # Wait for cleanup
#         await task

#         # Room should be cleaned up
#         assert room.id not in game_logic.game_manager.active_rooms


# class TestConcurrentOperations:
#     """Test concurrent operations and race conditions"""

#     # @pytest.mark.asyncio
#     async def test_concurrent_card_selections(self, game_logic, game_with_cards, players):
#         """Test concurrent card selections from multiple players"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         # Give players cards
#         for i, player in enumerate(players[1:3]):
#             player.handed_cards = [MemeCard(id=i+1, image_url=f"test{i+1}.jpg")]

#         # Simulate concurrent card selections
#         tasks = [
#             game_logic.player_select_card(game_with_cards, players[1].id, 1),
#             game_logic.player_select_card(game_with_cards, players[2].id, 2),
#         ]

#         results = await asyncio.gather(*tasks)

#         # Both should succeed
#         assert all(results)
#         assert len(game_with_cards.current_round.player_choices) == 2

#     # @pytest.mark.asyncio
#     async def test_concurrent_room_joins(self, game_logic, room, players):
#         """Test concurrent room joins"""
#         game_logic.game_manager.active_rooms[room.id] = room

#         # Simulate concurrent joins
#         tasks = [
#             game_logic.join_room(room.id, players[0]),
#             game_logic.join_room(room.id, players[1]),
#         ]

#         results = await asyncio.gather(*tasks, return_exceptions=True)

#         # At least one should succeed, but not both if they have same username
#         assert any(result is True for result in results if not isinstance(result, Exception))
