from django.core.exceptions import ValidationError
from django.test import TestCase
from game.models import (
    Card,
    DiscardPile,
    Game,
    GameParticipant,
    GameRound,
    GameSettings,
    Player,
    PlayerCard,
    Room,
    TooManyPlayersError,
)


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


class TestGameParticipantModel(TestCase):
    def setUp(self):
        self.player = Player.objects.create(username="test player")
        self.owner = Player.objects.create(username="owner")
        self.room = Room.objects.create(owner=self.owner)
        self.game = Game.objects.create(room=self.room)

    def test_create_participant(self):
        participant = GameParticipant.objects.create(game=self.game, player=self.player)
        self.assertEqual(participant.game, self.game)
        self.assertEqual(participant.player, self.player)
        self.assertEqual(participant.score, 0)

    def test_player_cant_join_same_game_twice(self):
        GameParticipant.objects.create(game=self.game, player=self.player)
        with self.assertRaises(Exception):
            GameParticipant.objects.create(game=self.game, player=self.player)

    def test_game_player_relation(self):
        participant = GameParticipant.objects.create(game=self.game, player=self.player)
        self.assertIn(participant, self.game.participants.all())
        self.assertIn(participant, self.player.games.all())

        self.game.delete()
        self.assertFalse(GameParticipant.objects.exists())


class TestGameSettingsModel(TestCase):
    def setUp(self):
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)

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
    def setUp(self) -> None:
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            game=self.game, player=self.player
        )
        self.card = Card.objects.create(type="situation", text="some cringe situation")
        self.new_card = Card.objects.create(
            type="situation", text="more cringe situation"
        )

    def test_create_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participant, situation_card=self.card
        )
        self.assertEqual(game_round.game, self.game)
        self.assertEqual(game_round.number, 1)
        self.assertEqual(game_round.leader, self.participant)
        self.assertEqual(game_round.situation_card, self.card)

    def test_update_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participant, situation_card=self.card
        )
        game_round.number = 2
        game_round.situation_card = self.new_card
        game_round.save()
        self.assertEqual(game_round.game, self.game)
        self.assertEqual(game_round.number, 2)
        self.assertEqual(game_round.leader, self.participant)
        self.assertEqual(game_round.situation_card, self.new_card)

    def test_delete_round(self) -> None:
        game_round = GameRound.objects.create(
            game=self.game, leader=self.participant, situation_card=self.card
        )
        round_id = game_round.id
        game_round.delete()
        self.assertFalse(GameRound.objects.filter(id=round_id).exists())


class TestPlayerCardModel(TestCase):
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
