import pytest

from app.game.dataclasses import Game, Player, Room
from app.game.enums import GameState


class TestPlayer:
    async def test_create_player(self):
        player = Player(id="1", username="Lisaveta")
        assert player.id == "1"
        assert player.username == "Lisaveta"
        assert player.handed_cards == []
        assert not player.is_host
        assert player.score == 0
        assert player.is_connected
        assert player.connection_order == 0

    async def test_update_player(self, test_player):
        old_username = test_player.username
        test_player.username = "Oleg"

        assert old_username != test_player.username


class TestRoom:
    async def test_create_room(self, test_player):
        room = Room(owner=test_player)
        assert isinstance(room.id, str)
        assert room.max_players == 10
        assert room.owner == test_player
        assert not room.is_private
        assert len(room.players) == 1
        assert test_player in room.players

    async def test_add_player(self, test_room):
        player = Player(id="2")

        players_quantity = len(test_room.players)

        test_room.add_player(player)

        assert players_quantity != len(test_room.players)
        assert len(test_room.players) == 2
        assert test_room.owner in test_room.players
        assert player in test_room.players

    async def test_add_player__already_joined(self, test_room):
        player = Player(id="2")
        test_room.add_player(player)

        with pytest.raises(Exception) as e:
            await test_room.add_player(player)

        assert "already joined" in str(e.value)

    async def test_add_player__room_is_full(self, test_room):
        test_room.max_players = 1
        player = Player(id="2")

        with pytest.raises(Exception) as e:
            test_room.add_player(player)

        assert "The room is full" in str(e.value)

    async def test_remove_player__not_found(self, test_room):
        player = Player(id="2")

        with pytest.raises(Exception) as e:
            test_room.remove_player(player)

        assert str(e.value) == "User not found"

    async def test_remove_player(self, test_room):
        player = Player(id="2")
        test_room.add_player(player)

        test_room.remove_player(player)

        assert len(test_room.players) == 1
        assert test_room.owner in test_room.players
        assert player not in test_room.players


class TestGame:
    def test_game_create(self, test_player):
        room = Room(owner=test_player)
        game = Game(room=room)

        assert isinstance(game.id, str)
        assert game.state == GameState.STARTING
        assert not game.current_round
        assert game.meme_deck == []
        assert game.situation_deck == []
        assert game.meme_discard_pile == {}
        assert game.situation_discard_pile == {}
        assert game.leader_index == 0


# class TestGameLogic:
#
#     def setup_method(self):
#         self.game_manager = get_game_manager()
#
#     async def test_start_game__not_enough_players(self, test_room):
#
#         with pytest.raises(Exception) as e:
#             await game_logic.prepare_game(room_id=test_room.id)
#
#         assert "Not enough players" in str(e.value)
#
#     async def test_start_game__room_not_found(self):
#
#         with pytest.raises(Exception) as e:
#             await game_logic.prepare_game("room")
#
#         assert str(e.value) == "Room not found"
#
#     async def test_start_game(self, test_room_with_players, mock_meme_cards, mock_situation_cards):
#
#         with (
#             patch("app.game.game.MemeService.MEME_CARDS", mock_meme_cards),
#             patch("app.game.game.SituationService.SITUATION_CARDS", mock_situation_cards),
#         ):
#             game = await game_logic.prepare_game(room_id=test_room_with_players.id)
#
#         assert test_room_with_players.id in self.game_manager.active_games
#         assert len(game.meme_deck) == len(mock_meme_cards) - len(game.players) * 6
#         assert len(game.situation_deck) == len(mock_situation_cards) - 1
#         assert game.current_round
#         assert game.current_round.round_number == 1
#         assert game.current_round.situation_card
#         assert not game.current_round.winner
#         assert game.meme_discard_pile == {}
#         assert game.situation_discard_pile == {}
#         for player in game.room.players:
#             assert len(player.handed_cards) == 6
#             assert len(set(player.handed_cards)) == 6
#
#     async def test_player_select_card(self, prepared_game):
#
#         for player in prepared_game.room.players:
#             if player != prepared_game.current_round.leader:
#                 await game_logic.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)
#
#         assert prepared_game.current_round.player_choices != {}
#         assert prepared_game.current_round.leader.id not in prepared_game.current_round.player_choices
#
#     # async def test_end_round(self, prepared_game):
#     #     for player in prepared_game.room.players:
#     #         if player != prepared_game.current_round.leader:
#     #             await game_logic.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)
#     #
#     #     winner = prepared_game.room.players[-1]
#     #     await game_logic.leader_choose_winner(prepared_game.room_id, winner.id)
#     #
#     #     await game_logic.end_round(prepared_game)
#     #
#     #     assert prepared_game.meme_discard_pile != {}
#     #     assert prepared_game.situation_discard_pile != {}
#     #     assert prepared_game.current_round.winner == winner
#     #     assert winner.score == 1
#     #     for player in prepared_game.room.players:
#     #         if prepared_game.current_round.leader != player:
#     #             assert len(player.handed_cards) == 5
#
#     # async def test_start_new_round(self, prepared_game):
#     #     initial_situation_card = prepared_game.current_round.situation_card
#     #     initial_round_number = prepared_game.current_round.round_number
#     #     initial_leader = prepared_game.current_round.leader
#     #
#     #     await game_logic.start_new_round(prepared_game)
#     #
#     #     assert prepared_game.current_round.round_number == initial_round_number + 1
#     #     assert prepared_game.current_round.situation_card != initial_situation_card
#     #     assert prepared_game.current_round.leader != initial_leader
#     #     # assert not prepared_game.current_round.winner
#     #     # assert prepared_game.current_round.player_choices == {}
#     #     # for player in prepared_game.room.players:
#     #     #     assert len(player.handed_cards) == 6
#
#     # async def test_hand_out_initial_cards(self, prepared_game):
#     #
#     #     full_meme_deck = len(prepared_game.meme_deck)
#     #
#     #     await game_logic.hand_out_initial_cards(prepared_game)
#     #
#     #     for player in prepared_game.room.players:
#     #         assert len(player.handed_cards) == 6
#     #         assert len(set(player.handed_cards)) == 6
#     #
#     #     assert len(prepared_game.meme_deck) == full_meme_deck - 4 * 6
#
#     # async def test_hand_out_initial_cards__not_enough_cards(self, test_game):
#     #     with pytest.raises(Exception) as e:
#     #         await game_logic.hand_out_initial_cards(test_game)
#     #
#     #     assert str(e.value) == "Not enough memes in deck"
#
#     # async def test_start_new_round(self, started_game):
#     #     initial_round = started_game.round_number
#     #     initial_leader = started_game.current_round.leader
#     #     initial_situation_card = started_game.current_round.situation_card
#     #
#     #     await game_logic.start_new_round(started_game)
#     #
#     #     assert initial_round != started_game.round_number
#     #     assert initial_leader != started_game.current_round.leader
#     #     assert initial_situation_card != started_game.current_round.situation_card
