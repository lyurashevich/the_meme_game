from django.core.exceptions import ValidationError
from django.test import TestCase
from game.models.card_models import Card, DiscardPile, PlayerCard
from game.models.game_models import Game, GameParticipant
from game.models.player_models import Player
from game.models.room_models import Room


class TestCardModel(TestCase):
    """
    Tests for Card model functionality
    - creation a meme card
    - creation a situation card
    - creation a card with invalid type
    - deletion of a card
    """

    def test_create_meme_card(self):
        card = Card.objects.create(type="meme", image_url="http://example.com/meme.jpg")
        self.assertEqual(card.type, "meme")
        self.assertEqual(card.image_url, "http://example.com/meme.jpg")
        self.assertIsNone(card.text)

    def test_create_situation_card(self):
        card = Card.objects.create(type="situation", text="some cringe situation")
        self.assertEqual(card.type, "situation")
        self.assertEqual(card.text, "some cringe situation")
        self.assertIsNone(card.image_url)

    def test_invalid_card_type(self):
        with self.assertRaises(ValidationError):
            card = Card(type="wrong", text="error")
            card.full_clean()

    def test_card_delete(self):
        card = Card.objects.create(type="meme", image_url="http://example.com/meme.jpg")
        card_id = card.id
        card.delete()
        with self.assertRaises(Card.DoesNotExist):
            Card.objects.get(id=card_id)


class TestPlayerCardModel(TestCase):
    """
    Tests PlayerCard model functionality:
    - creation of a player meme card
    - deletion of a player meme card
    """

    def setUp(self):
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            game=self.game, player=self.player
        )
        self.card = Card.objects.create(
            type="meme", image_url="http://example.com/meme.jpg"
        )

    def test_create_player_card(self):
        player_card = PlayerCard.objects.create(
            participant=self.participant, card=self.card, game=self.game
        )
        self.assertEqual(player_card.participant.id, self.participant.id)
        self.assertEqual(player_card.game.id, self.game.id)
        self.assertEqual(player_card.card.type, self.card.type)
        self.assertEqual(player_card.card.image_url, self.card.image_url)

    def test_delete_player_card(self):
        player_card = PlayerCard.objects.create(
            participant=self.participant, card=self.card, game=self.game
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
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.card = Card.objects.create(
            type="meme", image_url="http://example.com/meme.jpg"
        )

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
