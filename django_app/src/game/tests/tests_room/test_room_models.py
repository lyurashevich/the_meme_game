from django.test import TestCase
from game.models.player_models import Player
from game.models.room_models import Room, TooManyPlayersError


class TestRoomModel(TestCase):
    """
    Tests for room model functionality:
    - creating a room without name
    - creating a room with name
    - adding a player to the room
    - removing players from the room
    - max players limit
    - checking the room owner
    """

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
