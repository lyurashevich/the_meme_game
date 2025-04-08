from django.urls import reverse
from game.models import Player, Room, RoomCount
from rest_framework import status
from rest_framework.test import APITestCase


class TestListCreatePlayerEndpoints(APITestCase):
    """
    Tests for creating a player and getting a list endpoints:
    - getting a list of players
    - creating a player with username
    - creating a player without username
    """

    def setUp(self) -> None:
        self.player = Player.objects.create_user(username="test_player")
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
        self.assertEqual(response.data["username"], "new_player")

    def test_create_test_player_without_username(self) -> None:
        data: dict[str, str] = {}
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["username"].startswith("player"))
        self.assertEqual(Player.objects.count(), 2)


class TestDetailPlayerEndpoints(APITestCase):
    """
    Tests player endpoints:
    - getting player by ID
    - partial updating player by ID
    - deleting player by id
    """

    def setUp(self) -> None:
        self.player = Player.objects.create_user(username="test_player")
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


class TestCardViews(APITestCase):
    def setUp(self):
        self.meme_cards = reverse("get-meme-cards")
        self.situation_cards = reverse("get-situation-cards")

    def test_get_meme_cards(self):
        response = self.client.get(self.meme_cards)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_situation_cards(self):
        response = self.client.get(self.situation_cards)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestRoomsViews(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create_user()
        self.create_room = reverse("create-room")
        self.room_list = reverse("room-list")
        self.client.force_authenticate(user=self.owner)

    def test_create_room(self):
        response = self.client.post(self.create_room, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Room.objects.count(), 1)
        room = Room.objects.first()

        self.assertEqual(room.owner, self.owner)
        self.assertIn("room_token", response.data)

    def test_list_public_rooms(self):
        response = self.client.get(self.room_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_room_if_already_exists(self):

        response1 = self.client.post(self.create_room, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        room_id_1 = response1.data["id"]

        self.assertEqual(Room.objects.filter(owner=self.owner).count(), 1)

        response2 = self.client.post(self.create_room, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        room_id_2 = response2.data["id"]

        self.assertNotEqual(room_id_2, room_id_1)

        self.assertEqual(Room.objects.filter(owner=self.owner).count(), 1)
        room = Room.objects.get(owner=self.owner)
        self.assertEqual(str(room.id), room_id_2)


class UpdateRoomCountView(APITestCase):
    def setUp(self):
        self.url = reverse("update-active-rooms")

    def test_update_active_rooms(self):
        self.assertEqual(RoomCount.objects.count(), 0)

        data = {"active_rooms": 5}
        response = self.client.put(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoomCount.objects.count(), 1)
        self.assertEqual(RoomCount.objects.get(id=1).active_rooms, 5)
