from django.urls import reverse
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
)
from rest_framework import status
from rest_framework.test import APITestCase

####################################################
#                     PLAYER                       #
####################################################


class TestListCreatePlayerEndpoints(APITestCase):
    def setUp(self) -> None:
        self.player = Player.objects.create(username="test_player")
        self.list_url = reverse("player_list_create")

    def test_get_list_players(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "test_player")

    def test_create_test_player(self) -> None:
        data = {"username": "new_player"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Player.objects.count(), 2)

    def test_create_test_player_without_username(self) -> None:
        data: dict[str, str] = {}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["username"].startswith("player"))
        self.assertEqual(Player.objects.count(), 2)


class TestDetailPlayerEndpoints(APITestCase):
    def setUp(self) -> None:
        self.player = Player.objects.create(username="test_player")
        self.room = Room.objects.create(name="test_room", owner=self.player)
        self.detail_url = reverse("player_detail", kwargs={"pk": int(self.player.id)})

    def test_get_player_by_id(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "test_player")

    def test_update_player(self) -> None:
        data = {"username": "updated_name"}
        response = self.client.patch(self.detail_url, data=data, format="json")
        self.player.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.player.username, "updated_name")

    def test_delete_player(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Player.objects.count(), 0)


####################################################
#                     ROOM                         #
####################################################


class TestListCreateRoomEndpoints(APITestCase):
    def setUp(self) -> None:
        self.player = Player.objects.create(username="test_player")
        self.list_url = reverse("player_list_create")

    def test_get_list_players(self) -> None:
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "test_player")

    def test_create_test_player(self) -> None:
        data = {"username": "new_player"}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Player.objects.count(), 2)

    def test_create_test_player_without_username(self) -> None:
        data: dict[str, str] = {}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["username"].startswith("player"))
        self.assertEqual(Player.objects.count(), 2)


class TestDetailRoomEndpoints(APITestCase):
    def setUp(self) -> None:
        self.player = Player.objects.create(username="test_player")
        self.detail_url = reverse("player_detail", kwargs={"pk": int(self.player.id)})

    def test_get_player_by_id(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "test_player")

    def test_update_player(self) -> None:
        data = {"username": "updated_name"}
        response = self.client.patch(self.detail_url, data=data, format="json")
        self.player.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.player.username, "updated_name")

    def test_delete_player(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Player.objects.count(), 0)


####################################################
#                       CARDS                      #
####################################################


class TestCardsViews(APITestCase):
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


####################################################
#                       GAME                      #
####################################################


class TestGameViews(APITestCase):
    def setUp(self) -> None:
        self.owner = Player.objects.create()
        self.player = Player.objects.create()

        self.room = Room.objects.create(owner=self.owner)
        self.game = Game.objects.create(room=self.room)

    def test_start_game_not_by_owner(self) -> None:
        self.url = reverse("start_game", args=[self.room.id])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Game.objects.filter(id=self.game.id).exists())

        game = Game.objects.get(id=self.game.id)
        self.assertEqual(game.room, self.room)

    def test_start_game_by_owner(self) -> None:
        pass

    def test_end_game(self) -> None:
        self.url = reverse("end_game", args=[str(self.game.id)])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "the game ended and deleted"})

        with self.assertRaises(Game.DoesNotExist):
            Game.objects.get(id=self.game.id)


####################################################
#               GAME PARTICIPANT                   #
####################################################


class TestListCreateParticipantView(APITestCase):
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


####################################################
#                  GAME SETTINGS                   #
####################################################


class TestDetailSettingsView(APITestCase):
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


####################################################
#                     ROUND                        #
####################################################


class TestGameRoundView(APITestCase):
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


####################################################
#                CARDS IN GAME                     #
####################################################


class TestPlayerCardView(APITestCase):
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
