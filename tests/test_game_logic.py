# import pytest
# import asyncio
# from unittest.mock import AsyncMock, MagicMock, patch
# from datetime import datetime, timedelta

# from app.game import GameLogic
# from app.models import (
#     Game, GameManager, GameRound, GameSettings, GameState,
#     MemeCard, Player, Room, RoundState, SituationCard
# )


# @pytest.fixture
# def game_logic():
#     return GameLogic()


# @pytest.fixture
# def players():
#     return [
#         Player(id=1, username="Alice", connection_order=0),
#         Player(id=2, username="Bob", connection_order=1),
#         Player(id=3, username="Charlie", connection_order=2),
#         Player(id=4, username="Diana", connection_order=3),
#     ]


# @pytest.fixture
# def meme_cards():
#     return [MemeCard(id=i, image_url=f"https://example.com/meme_{i}.jpg") for i in range(1, 21)]


# @pytest.fixture
# def situation_cards():
#     return [SituationCard(id=i, text=f"Situation {i}") for i in range(1, 11)]


# @pytest.fixture
# def room(players):
#     room = Room(name="Test Room", max_players=6)
#     room.players = players[:3]  # Start with 3 players
#     room.owner = players[0]
#     return room


# @pytest.fixture
# def game_with_cards(room, meme_cards, situation_cards):
#     game = Game(room=room, state=GameState.WAITING)
#     game.meme_deck = meme_cards.copy()
#     game.situation_deck = situation_cards.copy()
#     return game


# class TestRoomManagement:
#     """Test room creation, joining, and leaving functionality"""

#     # @pytest.mark.asyncio
#     async def test_create_room_success(self, game_logic):
#         """Test successful room creation"""
#         room = await game_logic.create_room("Test Room", max_players=6, is_private=False)

#         assert room.name == "Test Room"
#         assert room.max_players == 6
#         assert room.is_private == False
#         assert room.id in game_logic.game_manager.active_rooms
#         assert len(room.players) == 0

#     # @pytest.mark.asyncio
#     @pytest.mark.parametrize("room_name,max_players,is_private", [
#         ("Room 1", 4, True),
#         ("Room 2", 10, False),
#         ("", 2, True),
#         ("Very Long Room Name That Should Still Work", 8, False),
#     ])
#     async def test_create_room_with_different_params(self, game_logic, room_name, max_players, is_private):
#         """Test room creation with various parameters"""
#         room = await game_logic.create_room(room_name, max_players, is_private)

#         assert room.name == room_name
#         assert room.max_players == max_players
#         assert room.is_private == is_private

#     # @pytest.mark.asyncio
#     async def test_join_room_success(self, game_logic, room, players):
#         """Test successful player joining room"""
#         # Add room to active rooms
#         game_logic.game_manager.active_rooms[room.id] = room

#         # First player joins (becomes owner)
#         result = await game_logic.join_room(room.id, players[0])
#         assert result == True
#         assert players[0] in room.players
#         assert room.owner == players[0]
#         assert players[0].is_host == True

#     # @pytest.mark.asyncio
#     async def test_join_room_username_uniqueness(self, game_logic, room, players):
#         """Test username uniqueness validation within room"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         room.players.append(players[0])

#         # Try to join with same username (case insensitive)
#         duplicate_player = Player(id=5, username="alice")  # lowercase

#         with pytest.raises(Exception, match="Username already exists"):
#             await game_logic.join_room(room.id, duplicate_player)

#     # @pytest.mark.asyncio
#     async def test_join_room_full(self, game_logic, room, players):
#         """Test joining full room"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         room.max_players = 2
#         room.players = players[:2]  # Room is full

#         with pytest.raises(Exception, match="Room is full"):
#             await game_logic.join_room(room.id, players[2])

#     # @pytest.mark.asyncio
#     async def test_join_nonexistent_room(self, game_logic, players):
#         """Test joining non-existent room"""
#         with pytest.raises(Exception, match="Room not found"):
#             await game_logic.join_room("nonexistent_room_id", players[0])

#     # @pytest.mark.asyncio
#     async def test_leave_room_success(self, game_logic, room, players):
#         """Test successful player leaving room"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         game_logic.game_manager.player_connections[players[0].id] = room.id
#         room.players.append(players[0])

#         result = await game_logic.leave_room(players[0].id)
#         assert result == True
#         assert players[0] not in room.players
#         assert players[0].id not in game_logic.game_manager.player_connections

#     # @pytest.mark.asyncio
#     async def test_leave_room_cleanup_when_empty(self, game_logic, room, players):
#         """Test room cleanup when last player leaves"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         game_logic.game_manager.player_connections[players[0].id] = room.id
#         room.players = [players[0]]  # Only one player

#         await game_logic.leave_room(players[0].id)

#         # Room should be cleaned up
#         assert room.id not in game_logic.game_manager.active_rooms
#         assert players[0].id not in game_logic.game_manager.player_connections

#     # @pytest.mark.asyncio
#     async def test_leave_nonexistent_player(self, game_logic):
#         """Test leaving with non-existent player"""
#         with pytest.raises(Exception, match="Player not found"):
#             await game_logic.leave_room(999)


# class TestGameStart:
#     """Test game initialization and starting"""

#     # @pytest.mark.asyncio
#     async def test_start_game_success(self, game_logic, room, meme_cards, situation_cards):
#         """Test successful game start"""
#         game_logic.game_manager.active_rooms[room.id] = room

#         # Mock card service
#         mock_card_service = AsyncMock()
#         mock_card_service.get_meme_cards.return_value = meme_cards
#         mock_card_service.get_situation_cards.return_value = situation_cards
#         game_logic.card_service = mock_card_service

#         result = await game_logic.start_game(room.id)

#         assert result == True
#         assert room.id in game_logic.game_manager.active_games
#         game = game_logic.game_manager.active_games[room.id]
#         assert game.state == GameState.IN_PROGRESS
#         assert game.round_number == 1
#         assert game.current_round is not None

#     # @pytest.mark.asyncio
#     async def test_start_game_insufficient_players(self, game_logic, room, players):
#         """Test starting game with insufficient players"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         room.players = players[:2]  # Only 2 players (need 3)

#         with pytest.raises(Exception, match="Not enough players"):
#             await game_logic.start_game(room.id)

#     # @pytest.mark.asyncio
#     async def test_start_nonexistent_room(self, game_logic):
#         """Test starting game in non-existent room"""
#         with pytest.raises(Exception, match="Room not found"):
#             await game_logic.start_game("nonexistent_room_id")

#     # @pytest.mark.asyncio
#     async def test_hand_out_initial_cards(self, game_logic, game_with_cards, players):
#         """Test initial card distribution"""
#         game_with_cards.room.players = players[:3]

#         await game_logic.hand_out_initial_cards(game_with_cards)

#         # Each player should have 6 cards
#         for player in game_with_cards.room.players:
#             assert len(player.handed_cards) == 6

#         # Deck should be reduced
#         expected_remaining = len(game_with_cards.meme_deck) - (3 * 6)
#         assert len(game_with_cards.meme_deck) == expected_remaining

#     # @pytest.mark.asyncio
#     async def test_hand_out_initial_cards_insufficient_cards(self, game_logic, game_with_cards, players):
#         """Test card distribution when not enough cards"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.meme_deck = [MemeCard(id=1, image_url="test.jpg")]  # Only 1 card

#         await game_logic.hand_out_initial_cards(game_with_cards)

#         # Players should get what's available
#         total_cards_distributed = sum(len(p.handed_cards) for p in game_with_cards.room.players)
#         assert total_cards_distributed == 1


# class TestRoundManagement:
#     """Test round creation, card selection, and winner choosing"""

#     # @pytest.mark.asyncio
#     async def test_start_new_round_success(self, game_logic, game_with_cards, players):
#         """Test successful round start"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.leader_index = 0

#         await game_logic.start_new_round(game_with_cards)

#         assert game_with_cards.round_number == 1
#         assert game_with_cards.current_round is not None
#         assert game_with_cards.current_round.leader == players[0]
#         assert game_with_cards.current_round.situation_card is not None
#         assert game_with_cards.state == GameState.ROUND_ACTIVE

#     # @pytest.mark.asyncio
#     async def test_start_new_round_no_situation_cards(self, game_logic, game_with_cards, players):
#         """Test round start when no situation cards available"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.situation_deck = []  # No situation cards

#         with pytest.raises(Exception, match="No situation cards available"):
#             await game_logic.start_new_round(game_with_cards)

#     # @pytest.mark.asyncio
#     async def test_player_select_card_success(self, game_logic, game_with_cards, players):
#         """Test successful card selection"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         # Give player a card
#         players[1].handed_cards = [MemeCard(id=1, image_url="test.jpg")]

#         result = await game_logic.player_select_card(game_with_cards, players[1].id, 1)

#         assert result == True
#         assert players[1].id in game_with_cards.current_round.player_choices
#         assert game_with_cards.current_round.player_choices[players[1].id].id == 1

#     # @pytest.mark.asyncio
#     async def test_player_select_card_leader_cannot_select(self, game_logic, game_with_cards, players):
#         """Test that leader cannot select cards"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         result = await game_logic.player_select_card(game_with_cards, players[0].id, 1)

#         assert result == False

#     # @pytest.mark.asyncio
#     async def test_player_select_card_invalid_card(self, game_logic, game_with_cards, players):
#         """Test selecting invalid card"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         players[1].handed_cards = [MemeCard(id=1, image_url="test.jpg")]

#         result = await game_logic.player_select_card(game_with_cards, players[1].id, 999)

#         assert result == False

#     # @pytest.mark.asyncio
#     async def test_player_select_card_wrong_round_state(self, game_logic, game_with_cards, players):
#         """Test card selection in wrong round state"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.LEADER_CHOOSING  # Wrong state

#         result = await game_logic.player_select_card(game_with_cards, players[1].id, 1)

#         assert result == False

#     # @pytest.mark.asyncio
#     async def test_leader_choose_winner_success(self, game_logic, game_with_cards, players):
#         """Test successful winner selection by leader"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.LEADER_CHOOSING
#         game_with_cards.current_round.player_choices = {players[1].id: MemeCard(id=1, image_url="test.jpg")}

#         result = await game_logic.leader_choose_winner(game_with_cards, players[1].id)

#         assert result == True
#         assert game_with_cards.current_round.winner == players[1]
#         assert players[1].score == 1

#     # @pytest.mark.asyncio
#     async def test_leader_choose_winner_cannot_choose_self(self, game_logic, game_with_cards, players):
#         """Test that leader cannot choose themselves as winner"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.LEADER_CHOOSING

#         result = await game_logic.leader_choose_winner(game_with_cards, players[0].id)

#         assert result == False

#     # @pytest.mark.asyncio
#     async def test_leader_choose_winner_wrong_state(self, game_logic, game_with_cards, players):
#         """Test winner selection in wrong round state"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS  # Wrong state

#         result = await game_logic.leader_choose_winner(game_with_cards, players[1].id)

#         assert result == False


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
#     async def test_should_end_game_score_limit(self, game_logic, game_with_cards, players, score_to_win, player_scores, should_end):
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
#     async def test_should_end_game_max_rounds(self, game_logic, game_with_cards, max_rounds, current_round, should_end):
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
