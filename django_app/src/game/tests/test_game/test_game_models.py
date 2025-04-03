from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from game.models.card_models import SituationCard
from game.models.game_models import Game, GameParticipant, GameSettings
from game.models.game_round_models import GameRound
from game.models.player_models import Player


class TestGameModel(TestCase):
    """
    Tests for game model functionality:
    - deleting of a room
    """

    def setUp(self):
        self.player = Player.objects.create_user()
        self.game = Game.objects.create(owner=self.player)

    def test_game_delete(self):
        game_id = self.game.id
        self.game.delete()
        with self.assertRaises(Game.DoesNotExist):
            Game.objects.get(id=game_id)

        self.assertFalse(Game.objects.filter(id=game_id).exists())


class TestGameParticipantModel(TestCase):
    """
    Tests for game participant model functionality:
    - creating of a game participant
    - trying to join the game twice
    - the player relation
    """

    def setUp(self):
        self.player = Player.objects.create_user(username="test player")
        self.owner = Player.objects.create_user(username="owner")
        self.game = Game.objects.create(owner=self.owner)

    def test_create_participant(self):
        self.assertEqual(self.game.participants.all().count(), 1)
        self.game.add_player(self.player)
        self.assertEqual(self.game.participants.all().count(), 2)
        self.assertIn(
            list(self.game.participants.all())[0], GameParticipant.objects.all()
        )
        self.assertEqual(list(self.game.participants.all())[0].score, 0)

    def test_player_cant_join_same_game_twice(self):
        self.game.add_player(self.player)
        self.assertEqual(self.game.participants.all().count(), 2)
        with self.assertRaises(IntegrityError):
            self.game.add_player(self.player)


class TestGameSettingsModel(TestCase):
    """
    Tests for game settings models functionality:
    - creating game settings
    - creating game setting with wrong data
    - updating the game settings
    - deleting the game settings
    - checking if game settings delete with the game
    """

    def setUp(self):
        self.player = Player.objects.create_user()
        self.game = Game.objects.create(owner=self.player)

    def test_create_game_settings(self):
        settings = GameSettings.objects.create(game=self.game)
        self.assertEqual(settings.game.id, self.game.id)
        self.assertEqual(settings.time_per_turn, 60)
        self.assertEqual(settings.time_to_choose_winner, 60)
        self.assertEqual(settings.score_limit, 0)
        self.assertTrue(GameSettings.objects.filter(id=settings.id).exists())

    def test_create_game_settings_with_invalid_data(self):
        invalid_data = [
            {"game": self.game, "time_per_turn": 29, "time_to_choose_winner": 10},
            {"game": self.game, "time_per_turn": 200, "time_to_choose_winner": 200},
            {"game": self.game, "score_limit": -9},
        ]

        for data in invalid_data:
            with self.subTest(data=data):
                with self.assertRaises(ValidationError):
                    settings = GameSettings(**data)
                    settings.full_clean()

    def test_update_game_settings(self):
        settings = GameSettings.objects.create(game=self.game)
        settings.time_per_turn = 90
        settings.save()
        self.assertEqual(settings.time_per_turn, 90)
        settings.refresh_from_db()
        self.assertEqual(settings.time_per_turn, 90)
        self.assertEqual(settings.time_to_choose_winner, 60)
        self.assertEqual(settings.score_limit, 0)

    def test_delete_game_settings(self):
        settings = GameSettings.objects.create(game=self.game)
        settings_id = settings.id
        settings.delete()
        self.assertFalse(GameSettings.objects.filter(id=settings_id).exists())

    def test_delete_game_settings_with_game(self):
        settings = GameSettings.objects.create(game=self.game)
        settings_id = settings.id
        self.game.delete()
        self.assertFalse(GameSettings.objects.filter(id=settings_id).exists())


class TestRoundModel(TestCase):
    """
    Tests for game round model functionality:
    - creating a round
    - updating the round
    - deleting the round
    """

    def setUp(self) -> None:
        self.player = Player.objects.create_user()
        self.game = Game.objects.create(owner=self.player)
        self.card = SituationCard.objects.create(text="some cringe situation")
        self.new_card = SituationCard.objects.create(text="more cringe situation")
        self.participants = list(self.game.participants.all())

    def test_create_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participants[0], situation_card=self.card
        )
        self.assertEqual(game_round.game, self.game)
        self.assertEqual(game_round.number, 1)
        self.assertIn(game_round.leader, self.game.participants.all())
        self.assertEqual(game_round.situation_card, self.card)

    def test_update_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participants[0], situation_card=self.card
        )
        game_round.number = 2
        game_round.situation_card = self.new_card
        game_round.save()
        self.assertEqual(game_round.game, self.game)
        self.assertEqual(game_round.number, 2)
        self.assertEqual(game_round.leader, self.participants[0])
        self.assertEqual(game_round.situation_card, self.new_card)

    def test_delete_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participants[0], situation_card=self.card
        )
        round_id = game_round.id
        game_round.delete()
        self.assertFalse(GameRound.objects.filter(id=round_id).exists())
