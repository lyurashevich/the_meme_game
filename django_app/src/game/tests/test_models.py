from django.test import TestCase
from game.models import MemeCard, Player, Room, SituationCard


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


class TestPlayerModel(TestCase):
    """
    Tests for player model functionality:
    - creating a user with username
    - creating a user without username
    - updating the user
    - deleting the user
    """

    def test_create_player_with_username(self):
        player = Player.objects.create_user(username="username")
        self.assertTrue(Player.objects.filter(id=player.id).exists())
        self.assertEqual(player.username, "username")

    def test_create_player_without_username(self):
        player = Player.objects.create_user()
        self.assertTrue(Player.objects.filter(id=player.id).exists())
        self.assertTrue(player.username.startswith("player"))

    def test_update_player(self):
        player = Player.objects.create_user(username="username")
        player.username = "new_username"
        player.save()
        self.assertNotEqual(player.username, "username")
        self.assertEqual(player.username, "new_username")

    def test_delete_player(self):
        player = Player.objects.create_user()
        player_id = player.id
        player.delete()
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(id=player_id)


class TestRoomModel(TestCase):
    """
    Tests for game model functionality:
    - deleting of a room
    """

    def setUp(self):
        self.player = Player.objects.create_user()
        self.game = Room.objects.create(owner=self.player)

    def test_game_delete(self):
        game_id = self.game.id
        self.game.delete()
        with self.assertRaises(Room.DoesNotExist):
            Room.objects.get(id=game_id)

        self.assertFalse(Room.objects.filter(id=game_id).exists())
