from django.urls import reverse
from game.models.card_models import Card
from game.models.game_models import Game, GameParticipant, GameSettings
from game.models.game_round_models import GameRound
from game.models.player_models import Player
from game.models.room_models import Room
from rest_framework import status
from rest_framework.test import APITestCase


class TestGameViews(APITestCase):
    """
    Tests game endpoints:
    - starting a game by a non-owner
    - ending a game
    """

    def setUp(self) -> None:
        self.owner = Player.objects.create()
        self.player = Player.objects.create()

        self.room = Room.objects.create(owner=self.owner)
        self.game = Game.objects.create(room=self.room)

    def test_start_game_not_by_owner(self) -> None:
        pass

    def test_start_game_by_owner(self) -> None:
        pass

    def test_end_game(self) -> None:
        self.url = reverse("end_game", args=[str(self.game.id)])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "the game ended and deleted"})

        with self.assertRaises(Game.DoesNotExist):
            Game.objects.get(id=self.game.id)


class TestListCreateParticipantView(APITestCase):
    """
    Tests game participant endpoints:
    - creating a game participant
    - getting a list of game participants
    """

    def setUp(self):
        self.url = reverse("participants-list")
        self.owner = Player.objects.create(username="owner")
        self.room = Room.objects.create(owner=self.owner)
        self.game = Game.objects.create(room=self.room)
        self.player = Player.objects.create(username="username")

    def test_create_participant(self) -> None:
        data = {"game": self.game.id, "player": self.player.id, "score": 0}
        initial_count = GameParticipant.objects.count()
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GameParticipant.objects.count(), initial_count + 1)
        self.assertTrue(
            GameParticipant.objects.filter(game=self.game, player=self.player).exists()
        )

    def test_get_list_of_participants(self) -> None:
        GameParticipant.objects.create(game=self.game, player=self.player)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["player"]), str(self.player.id))


class TestDetailParticipantView(APITestCase):
    """
    Tests game participants endpoints:
    - getting a game participant by ID
    - getting a game participant with wrong ID
    - deleting participant
    """

    def setUp(self) -> None:
        self.owner = Player.objects.create(username="owner")
        self.player = Player.objects.create(username="player")
        self.room = Room.objects.create(owner=self.owner)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            game=self.game, player=self.player
        )
        self.url = reverse(
            "participant-detail", kwargs={"pk": int(self.participant.id)}
        )

    def test_get_detail_participant(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.participant.id))
        self.assertEqual(response.data["score"], 0)

    def test_get_detail_wrong_participant(self) -> None:
        fake_url = reverse("participant-detail", kwargs={"pk": 999})
        response = self.client.get(fake_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_participant(self) -> None:
        initial_count = GameParticipant.objects.count()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GameParticipant.objects.count(), initial_count - 1)
        self.assertFalse(
            GameParticipant.objects.filter(id=self.participant.id).exists()
        )


class TestDetailSettingsView(APITestCase):
    """
    Tests game settings endpoints:
    - getting game setting by game ID
    - getting game settings with wrong game ID
    - partial updating game settings by game ID
    """

    def setUp(self) -> None:
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.settings = GameSettings.objects.create(game=self.game)
        self.url = reverse("game-settings", kwargs={"game_id": self.game.id})

    def test_get_game_settings(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["game"], self.game.id)
        self.assertEqual(response.data["time_per_turn"], 60)
        self.assertEqual(response.data["time_to_choose_winner"], 60)
        self.assertEqual(response.data["score_limit"], 0)

    def test_get_invalid_game_setting(self):
        fake_url = reverse("game-settings", kwargs={"game_id": 999})
        response = self.client.get(fake_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_game_settings(self) -> None:
        data = {"time_per_turn": 100}

        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["time_per_turn"], 100)
        self.assertEqual(response.data["time_to_choose_winner"], 60)
        self.assertEqual(response.data["score_limit"], 0)


class TestGameRoundView(APITestCase):
    """
    Tests for game round endpoints:
    - getting a round by game ID and round number
    - getting a round by game ID with wrong round number
    """

    def setUp(self) -> None:
        self.player = Player.objects.create()
        self.room = Room.objects.create(owner=self.player)
        self.game = Game.objects.create(room=self.room)
        self.participant = GameParticipant.objects.create(
            player=self.player, game=self.game
        )
        self.situation_card = Card.objects.create(
            type="situation", text="some cringe situation"
        )
        self.new_situation_card = Card.objects.create(
            type="situation", text="more cringe situation"
        )
        self.game_round = GameRound.objects.create(
            game=self.game, leader=self.participant, situation_card=self.situation_card
        )
        self.url = reverse(
            "get-round",
            kwargs={"game_id": self.game.id, "number": self.game_round.number},
        )

    def test_get_game_round(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["game"], self.game.id)
        self.assertEqual(response.data["number"], 1)
        self.assertEqual(response.data["leader"], self.participant.id)
        self.assertEqual(response.data["situation_card"], self.situation_card.id)

    def test_get_invalid_game_round(self) -> None:
        fake_url = reverse("get-round", kwargs={"game_id": self.game.id, "number": 500})
        response = self.client.get(fake_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_game_round(self) -> None:
        data = {"number": 2, "situation_card": self.new_situation_card.id}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["game"], self.game.id)
        self.assertEqual(response.data["number"], 2)
        self.assertEqual(response.data["leader"], self.participant.id)
        self.assertEqual(response.data["situation_card"], self.new_situation_card.id)
