from django.test import TestCase
from game.models.player_models import Player


class TestPlayerModel(TestCase):
    """
    Tests for player model functionality:
    - creating a user with username
    - creating a user without username
    - updating the user
    - deleting the user
    """

    def test_create_player_with_username(self):
        player = Player.objects.create(username="username")
        self.assertEqual(player.username, "username")

    def test_create_player_without_username(self):
        player = Player.objects.create()
        self.assertEqual(player.username, f"player{player.id}")

    def test_update_player(self):
        player = Player.objects.create(username="username")
        player.username = "new_username"
        original_created_at = player.created_at
        player.save()
        self.assertNotEqual(player.username, "username")
        self.assertEqual(player.username, "new_username")
        self.assertEqual(player.created_at, original_created_at)

    def test_delete_player(self):
        player = Player.objects.create()
        player_id = player.id
        player.delete()
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(id=player_id)
