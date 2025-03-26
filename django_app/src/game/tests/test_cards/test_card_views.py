from django.urls import reverse
from game.models.card_models import Card, DiscardPile, PlayerCard
from game.models.game_models import Game, GameParticipant
from game.models.player_models import Player
from game.models.room_models import Room
from rest_framework import status
from rest_framework.test import APITestCase


class TestCardsViews(APITestCase):
    """
    Tests for card distribution endpoints:
    - initial 6 cards distribution
    - invalid card type handling
    - handling one meme card
    - handling one situation card
    """

    def setUp(self) -> None:
        self.meme_cards = [
            Card.objects.create(
                type="meme", image_url=f"http://example.com/meme{i}.jpg"
            )
            for i in range(6)
        ]
        self.situation_card = Card.objects.create(
            type="situation", text="some cringe situation"
        )

    def test_start_game_hand_out_view(self) -> None:
        self.url = reverse("get_six_cards")
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for card in response.data:
            self.assertIn("id", card)
            self.assertIn("type", card)
            self.assertIn("image_url", card)
            self.assertNotIn("text", card)

    def test_hand_out_wrong_type_card(self) -> None:
        self.url = reverse("get_one_card") + "?type=wrong"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "invalid card type")

    def test_hand_out_one_meme_card(self) -> None:
        self.url = reverse("get_one_card") + "?type=meme"
        response = self.client.get(self.url, {"type": "meme"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "meme")
        self.assertIn("image_url", response.data)
        self.assertNotIn("text", response.data)

    def test_hand_out_one_situation_card(self) -> None:
        self.url = reverse("get_one_card") + "?type=situation"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "situation")
        self.assertIn("text", response.data)
        self.assertNotIn("image_url", response.data)


class TestPlayerCardView(APITestCase):
    """
    Tests player's card collection endpoints:
    - retrieving player's cards
    """

    def setUp(self) -> None:
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            player=self.player, game=self.game
        )
        self.url = reverse(
            "player-cards",
            kwargs={"game_id": self.game.id, "participant_id": self.participant.id},
        )
        self.card = Card.objects.create(
            type="meme", image_url="http://example.com/meme.jpg"
        )
        self.player_card = PlayerCard.objects.create(
            participant=self.participant, card=self.card, game=self.game
        )

    def test_get_player_cards(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["participant"], self.participant.id)
        self.assertEqual(response.data[0]["game"], self.game.id)
        self.assertEqual(response.data[0]["card"], self.card.id)


class TestDiscardPileView(APITestCase):
    """
    Tests discard pile endpoints:
    - retrieve discard pile contents.
    """

    def setUp(self) -> None:
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            player=self.player, game=self.game
        )
        self.url = reverse("discard-cards", kwargs={"game_id": self.game.id})
        self.card = Card.objects.create(
            type="meme", image_url="http://example.com/meme.jpg"
        )
        self.discard_card = DiscardPile.objects.create(
            game=self.game, card=self.card, round_expires=10
        )

    def test_get_discard_pile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["game"], self.game.id)
        self.assertEqual(response.data[0]["card"], self.card.id)
        self.assertEqual(response.data[0]["round_expires"], 10)
