from django.urls import reverse
from game.models.player_models import Player
from rest_framework import status
from rest_framework.test import APITestCase


class TestListCreateRoomEndpoints(APITestCase):
    """
    Tests for creating a room and getting list of rooms

    """

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
