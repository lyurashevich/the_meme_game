from django.core.exceptions import ValidationError
from django.test import TestCase
from game.models import Card, Game, Player, Room, TooManyPlayersError


class TestPlayerModel(TestCase):

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

    def test_username_length(self):
        player = Player.objects.create(username="*" * 50)
        self.assertLessEqual(len(player.username), 50)


class TestCardModel(TestCase):
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


class TestRoomModel(TestCase):
    def setUp(self):
        self.player = Player.objects.create(username="owner")

    def test_create_room_without_name(self):
        room = Room.objects.create(owner=self.player)
        self.assertTrue(room.name.startswith("room"))
        self.assertEqual(room.owner, self.player)

    def test_create_room_with_name(self):
        room = Room.objects.create(name="nice room", owner=self.player)
        self.assertEqual(room.name, "nice room")

    def test_add_players_to_room(self):

        room = Room.objects.create(owner=self.player)
        player1 = Player.objects.create()

        room.players.add(player1)

        self.assertEqual(room.players.count(), 2)
        self.assertIn(player1, room.players.all())
        self.assertIn(self.player, room.players.all())

    def remove_players_from_room(self):

        room = Room.objects.create(owner=self.player)
        player1 = Player.objects.create()

        room.players.add(player1)
        room.players.remove(player1)

        self.assertEqual(room.players.count(), 1)
        self.assertNotIn(player1, room.players.all())
        self.assertIn(self.player, room.players.all())

    def test_max_players_limit(self):

        room = Room.objects.create(owner=self.player, max_players=2)

        player1 = Player.objects.create()
        player2 = Player.objects.create()

        room.players.add(player1)

        with self.assertRaises(TooManyPlayersError):
            room.add_player(player2)

    def test_room_owner(self):
        room = Room.objects.create(owner=self.player)
        self.assertEqual(room.owner, self.player)


class TestGameModel(TestCase):
    def setUp(self):
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)

    def test_game_delete(self):
        game_id = self.game.id
        self.game.delete()
        with self.assertRaises(Game.DoesNotExist):
            Game.objects.get(id=game_id)

        self.assertFalse(Game.objects.filter(id=game_id).exists())
