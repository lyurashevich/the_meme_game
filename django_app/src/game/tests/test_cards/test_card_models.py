from django.test import TestCase
from game.models.card_models import DiscardPile, MemeCard, PlayerCard, SituationCard
from game.models.game_models import Game
from game.models.player_models import Player


class TestCardModel(TestCase):
    """
    Tests for Card model functionality
    - creation a meme card
    - creation a situation card
    - creation a card with invalid type
    - deletion of a card
    """

    def setUp(self):
        self.meme_card = MemeCard.objects.create(
            image_url="http://example.com/meme.jpg"
        )
        self.situation_card = SituationCard.objects.create(text="some cringe situation")

    def test_create_meme_card(self):
        self.assertEqual(self.meme_card.image_url, "http://example.com/meme.jpg")
        self.assertTrue(MemeCard.objects.filter(id=self.meme_card.id).exists())

    def test_create_situation_card(self):
        self.assertEqual(self.situation_card.text, "some cringe situation")
        self.assertTrue(
            SituationCard.objects.filter(id=self.situation_card.id).exists()
        )

    def test_meme_card_delete(self):
        card_id = self.meme_card.id
        self.meme_card.delete()
        with self.assertRaises(MemeCard.DoesNotExist):
            MemeCard.objects.get(id=card_id)

    def test_situation_card_delete(self):
        card_id = self.situation_card.id
        self.situation_card.delete()
        with self.assertRaises(SituationCard.DoesNotExist):
            SituationCard.objects.get(id=card_id)


class TestPlayerCardModel(TestCase):
    """
    Tests PlayerCard model functionality:
    - creation of a player meme card
    - deletion of a player meme card
    """

    def setUp(self):
        self.player = Player.objects.create()
        self.game = Game.objects.create(owner=self.player)
        self.card = MemeCard.objects.create(image_url="http://example.com/meme.jpg")

    def test_create_player_card(self):
        participants = list(self.game.participants.all())
        player_card = PlayerCard.objects.create(
            participant=participants[0], card=self.card, game=self.game
        )
        self.assertEqual(player_card.participant.id, participants[0].id)
        self.assertEqual(player_card.card.image_url, self.card.image_url)

    def test_delete_player_card(self):
        participants = list(self.game.participants.all())
        player_card = PlayerCard.objects.create(
            participant=participants[0], card=self.card, game=self.game
        )
        player_card_id = player_card.id
        player_card.delete()
        self.assertFalse(PlayerCard.objects.filter(id=player_card_id).exists())


class TestDiscardPileModel(TestCase):
    """
    Tests DiscardPile model functionality:
    - creating a discard card
    - deleting a discard card
    """

    def setUp(self):
        self.player = Player.objects.create_user()
        self.game = Game.objects.create(owner=self.player)
        self.card = MemeCard.objects.create(image_url="http://example.com/meme.jpg")

    def test_create_discard_card(self):
        discard_card = DiscardPile.objects.create(
            card=self.card, game=self.game, round_expires=10
        )
        self.assertEqual(discard_card.game, self.game)
        self.assertEqual(discard_card.card, self.card)
        self.assertEqual(discard_card.round_expires, 10)

    def test_delete_discard_card(self):
        discard_card = DiscardPile.objects.create(
            card=self.card, game=self.game, round_expires=10
        )
        discard_card_id = discard_card.id
        discard_card.delete()
        self.assertFalse(DiscardPile.objects.filter(id=discard_card_id).exists())
