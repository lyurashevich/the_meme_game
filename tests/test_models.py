# import pytest
# from datetime import datetime
# from app.models import (
#     Game, GameManager, GameRound, GameSettings, GameState,
#     MemeCard, Player, Room, RoundState, SituationCard
# )


# class TestPlayerModel:
#     """Test Player dataclass functionality"""

#     def test_player_creation(self):
#         """Test basic player creation"""
#         player = Player(id=1, username="Alice")

#         assert player.id == 1
#         assert player.username == "Alice"
#         assert player.hand_cards == []
#         assert player.is_host == False
#         assert player.score == 0
#         assert player.is_connected == True
#         assert player.connection_order == 0

#     def test_player_with_cards(self):
#         """Test player with handed cards"""
#         cards = [MemeCard(id=i, image_url=f"test{i}.jpg") for i in range(1, 4)]
#         player = Player(id=1, username="Alice", hand_cards=cards)

#         assert len(player.hand_cards) == 3
#         assert player.hand_cards[0].id == 1

#     def test_player_score_increment(self):
#         """Test player score increment"""
#         player = Player(id=1, username="Alice")

#         assert player.score == 0
#         player.score += 1
#         assert player.score == 1

#     @pytest.mark.parametrize("username,expected", [
#         ("Alice", "Alice"),
#         ("alice", "alice"),
#         ("ALICE", "ALICE"),
#         ("", ""),
#         ("Very Long Username That Should Still Work", "Very Long Username That Should Still Work"),
#     ])
#     def test_player_username_variations(self, username, expected):
#         """Test player with different username formats"""
#         player = Player(id=1, username=username)
#         assert player.username == expected


# class TestRoomModel:
#     """Test Room dataclass functionality"""

#     def test_room_creation(self):
#         """Test basic room creation"""
#         room = Room(name="Test Room")

#         assert room.name == "Test Room"
#         assert room.max_players == 10
#         assert room.owner is None
#         assert room.is_private == False
#         assert room.players == []
#         assert room.invitation_link.startswith("https://your-domain.com/join/")

#     def test_room_with_players(self):
#         """Test room with players"""
#         players = [Player(id=i, username=f"Player{i}") for i in range(1, 4)]
#         room = Room(name="Test Room", players=players)

#         assert len(room.players) == 3
#         assert room.players[0].username == "Player1"

#     def test_room_max_players_validation(self):
#         """Test room with different max_players values"""
#         room = Room(name="Test Room", max_players=4)
#         assert room.max_players == 4

#     def test_room_private_setting(self):
#         """Test private room setting"""
#         room = Room(name="Test Room", is_private=True)
#         assert room.is_private == True


# class TestGameRoundModel:
#     """Test GameRound dataclass functionality"""

#     def test_game_round_creation(self):
#         """Test basic GameRound creation"""
#         leader = Player(id=1, username="Leader")
#         situation = SituationCard(id=1, text="Test situation")
#         round_obj = GameRound(round_number=1, leader=leader, situation_card=situation)

#         assert round_obj.round_number == 1
#         assert round_obj.leader == leader
#         assert round_obj.situation_card == situation
#         assert round_obj.player_choices == {}
#         assert round_obj.winner is None
#         assert round_obj.state == RoundState.CHOOSING_CARDS
#         assert round_obj.time_limit == 60

#     def test_game_round_with_choices(self):
#         """Test GameRound with player choices"""
#         leader = Player(id=1, username="Leader")
#         situation = SituationCard(id=1, text="Test situation")
#         player1 = Player(id=2, username="Player1")
#         player2 = Player(id=3, username="Player2")

#         card1 = MemeCard(id=1, image_url="test1.jpg")
#         card2 = MemeCard(id=2, image_url="test2.jpg")

#         round_obj = GameRound(
#             round_number=1,
#             leader=leader,
#             situation_card=situation,
#             player_choices={player1.id: card1, player2.id: card2}
#         )

#         assert len(round_obj.player_choices) == 2
#         assert round_obj.player_choices[player1.id] == card1
#         assert round_obj.player_choices[player2.id] == card2

#     def test_game_round_with_winner(self):
#         """Test GameRound with winner"""
#         leader = Player(id=1, username="Leader")
#         situation = SituationCard(id=1, text="Test situation")
#         winner = Player(id=2, username="Winner")

#         round_obj = GameRound(
#             round_number=1,
#             leader=leader,
#             situation_card=situation,
#             winner=winner
#         )

#         assert round_obj.winner == winner

#     def test_game_round_state_transitions(self):
#         """Test GameRound state transitions"""
#         leader = Player(id=1, username="Leader")
#         situation = SituationCard(id=1, text="Test situation")
#         round_obj = GameRound(round_number=1, leader=leader, situation_card=situation)

#         assert round_obj.state == RoundState.CHOOSING_CARDS

#         round_obj.state = RoundState.LEADER_CHOOSING
#         assert round_obj.state == RoundState.LEADER_CHOOSING

#         round_obj.state = RoundState.ROUND_ENDED
#         assert round_obj.state == RoundState.ROUND_ENDED


# class TestGameModel:
#     """Test Game dataclass functionality"""

#     def test_game_creation(self):
#         """Test basic Game creation"""
#         room = Room(name="Test Room")
#         game = Game(room=room)

#         assert game.room == room
#         assert game.state == GameState.WAITING
#         assert game.current_round is None
#         assert game.round_number == 0
#         assert game.meme_deck == []
#         assert game.situation_deck == []
#         assert game.meme_discard_pile == []
#         assert game.situation_discard_pile == []
#         assert game.leader_index == 0

#     def test_game_with_decks(self):
#         """Test Game with card decks"""
#         room = Room(name="Test Room")
#         meme_cards = [MemeCard(id=i, image_url=f"meme{i}.jpg") for i in range(1, 4)]
#         situation_cards = [SituationCard(id=i, text=f"Situation {i}") for i in range(1, 3)]

#         game = Game(
#             room=room,
#             meme_deck=meme_cards,
#             situation_deck=situation_cards
#         )

#         assert len(game.meme_deck) == 3
#         assert len(game.situation_deck) == 2
#         assert game.meme_deck[0].id == 1
#         assert game.situation_deck[0].id == 1

#     def test_game_state_transitions(self):
#         """Test Game state transitions"""
#         room = Room(name="Test Room")
#         game = Game(room=room)

#         assert game.state == GameState.WAITING

#         game.state = GameState.STARTING
#         assert game.state == GameState.STARTING

#         game.state = GameState.IN_PROGRESS
#         assert game.state == GameState.IN_PROGRESS

#         game.state = GameState.ROUND_ACTIVE
#         assert game.state == GameState.ROUND_ACTIVE

#         game.state = GameState.ROUND_ENDING
#         assert game.state == GameState.ROUND_ENDING

#         game.state = GameState.FINISHED
#         assert game.state == GameState.FINISHED

#     def test_game_round_number_increment(self):
#         """Test Game round number increment"""
#         room = Room(name="Test Room")
#         game = Game(room=room)

#         assert game.round_number == 0

#         game.round_number += 1
#         assert game.round_number == 1

#     def test_game_leader_index_rotation(self):
#         """Test Game leader index rotation"""
#         room = Room(name="Test Room")
#         players = [Player(id=i, username=f"Player{i}") for i in range(1, 4)]
#         room.players = players
#         game = Game(room=room)

#         assert game.leader_index == 0

#         game.leader_index = (game.leader_index + 1) % len(room.players)
#         assert game.leader_index == 1

#         game.leader_index = (game.leader_index + 1) % len(room.players)
#         assert game.leader_index == 2

#         game.leader_index = (game.leader_index + 1) % len(room.players)
#         assert game.leader_index == 0  # Back to start


# class TestGameSettingsModel:
#     """Test GameSettings dataclass functionality"""

#     def test_default_game_settings(self):
#         """Test default GameSettings values"""
#         settings = GameSettings()

#         assert settings.cards_per_player == 6
#         assert settings.round_time_limit == 60
#         assert settings.meme_card_cooldown == 10
#         assert settings.situation_card_cooldown == 20
#         assert settings.max_rounds is None
#         assert settings.score_to_win is None

#     def test_custom_game_settings(self):
#         """Test custom GameSettings values"""
#         settings = GameSettings(
#             cards_per_player=8,
#             round_time_limit=90,
#             meme_card_cooldown=15,
#             situation_card_cooldown=25,
#             max_rounds=20,
#             score_to_win=10
#         )

#         assert settings.cards_per_player == 8
#         assert settings.round_time_limit == 90
#         assert settings.meme_card_cooldown == 15
#         assert settings.situation_card_cooldown == 25
#         assert settings.max_rounds == 20
#         assert settings.score_to_win == 10

#     @pytest.mark.parametrize("cards_per_player,round_time_limit,meme_cooldown,situation_cooldown", [
#         (4, 30, 5, 10),
#         (8, 120, 15, 30),
#         (10, 60, 20, 40),
#     ])
#     def test_game_settings_variations(self, cards_per_player, round_time_limit, meme_cooldown, situation_cooldown):
#         """Test GameSettings with various parameter combinations"""
#         settings = GameSettings(
#             cards_per_player=cards_per_player,
#             round_time_limit=round_time_limit,
#             meme_card_cooldown=meme_cooldown,
#             situation_card_cooldown=situation_cooldown
#         )

#         assert settings.cards_per_player == cards_per_player
#         assert settings.round_time_limit == round_time_limit
#         assert settings.meme_card_cooldown == meme_cooldown
#         assert settings.situation_card_cooldown == situation_cooldown


# class TestGameManagerModel:
#     """Test GameManager dataclass functionality"""

#     def test_game_manager_creation(self):
#         """Test basic GameManager creation"""
#         manager = GameManager()

#         assert manager.active_games == {}
#         assert manager.active_rooms == {}
#         assert manager.player_connections == {}

#     def test_game_manager_with_data(self):
#         """Test GameManager with active games and rooms"""
#         room = Room(name="Test Room")
#         game = Game(room=room)
#         player_id = 1
#         room_id = room.id

#         manager = GameManager()
#         manager.active_games[room_id] = game
#         manager.active_rooms[room_id] = room
#         manager.player_connections[player_id] = room_id

#         assert room_id in manager.active_games
#         assert room_id in manager.active_rooms
#         assert player_id in manager.player_connections
#         assert manager.player_connections[player_id] == room_id

#     def test_game_manager_multiple_games(self):
#         """Test GameManager with multiple games"""
#         manager = GameManager()

#         # Create multiple rooms and games
#         for i in range(3):
#             room = Room(name=f"Room {i}")
#             game = Game(room=room)
#             manager.active_games[room.id] = game
#             manager.active_rooms[room.id] = room

#         assert len(manager.active_games) == 3
#         assert len(manager.active_rooms) == 3

#     def test_game_manager_player_connections(self):
#         """Test GameManager player connections"""
#         manager = GameManager()

#         # Add player connections
#         connections = {1: "room1", 2: "room1", 3: "room2"}
#         manager.player_connections.update(connections)

#         assert len(manager.player_connections) == 3
#         assert manager.player_connections[1] == "room1"
#         assert manager.player_connections[2] == "room1"
#         assert manager.player_connections[3] == "room2"


# class TestEnums:
#     """Test enum functionality"""

#     def test_game_state_enum(self):
#         """Test GameState enum values"""
#         assert GameState.WAITING.value == "waiting"
#         assert GameState.STARTING.value == "starting"
#         assert GameState.IN_PROGRESS.value == "in_progress"
#         assert GameState.ROUND_ACTIVE.value == "round_active"
#         assert GameState.ROUND_ENDING.value == "round_ending"
#         assert GameState.FINISHED.value == "finished"

#     def test_round_state_enum(self):
#         """Test RoundState enum values"""
#         assert RoundState.CHOOSING_CARDS.value == "choosing_cards"
#         assert RoundState.LEADER_CHOOSING.value == "leader_choosing"
#         assert RoundState.ROUND_ENDED.value == "round_ended"

#     def test_enum_comparison(self):
#         """Test enum comparison"""
#         assert GameState.WAITING == GameState.WAITING
#         assert GameState.WAITING != GameState.STARTING
#         assert RoundState.CHOOSING_CARDS == RoundState.CHOOSING_CARDS
#         assert RoundState.CHOOSING_CARDS != RoundState.LEADER_CHOOSING


# class TestEdgeCases:
#     """Test edge cases and boundary conditions"""

#     def test_empty_card_decks(self):
#         """Test game with empty card decks"""
#         room = Room(name="Test Room")
#         game = Game(room=room, meme_deck=[], situation_deck=[])

#         assert len(game.meme_deck) == 0
#         assert len(game.situation_deck) == 0

#     def test_single_player_room(self):
#         """Test room with single player"""
#         player = Player(id=1, username="Solo")
#         room = Room(name="Solo Room", players=[player])

#         assert len(room.players) == 1
#         assert room.players[0] == player

#     def test_max_players_room(self):
#         """Test room with maximum players"""
#         players = [Player(id=i, username=f"Player{i}") for i in range(10)]
#         room = Room(name="Full Room", max_players=10, players=players)

#         assert len(room.players) == 10
#         assert room.max_players == 10

#     def test_negative_scores(self):
#         """Test player with negative score (edge case)"""
#         player = Player(id=1, username="Loser", score=-5)

#         assert player.score == -5

#     def test_zero_round_number(self):
#         """Test game with zero round number"""
#         room = Room(name="Test Room")
#         game = Game(room=room, round_number=0)

#         assert game.round_number == 0

#     def test_large_round_number(self):
#         """Test game with large round number"""
#         room = Room(name="Test Room")
#         game = Game(room=room, round_number=1000)

#         assert game.round_number == 1000

#     def test_unicode_usernames(self):
#         """Test player with unicode username"""
#         player = Player(id=1, username="玩家1")

#         assert player.username == "玩家1"

#     def test_very_long_username(self):
#         """Test player with very long username"""
#         long_username = "A" * 1000
#         player = Player(id=1, username=long_username)

#         assert player.username == long_username

#     def test_very_long_situation_text(self):
#         """Test situation card with very long text"""
#         long_text = "A" * 10000
#         card = SituationCard(id=1, text=long_text)

#         assert card.text == long_text
