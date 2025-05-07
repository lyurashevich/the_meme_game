from unittest.mock import MagicMock, patch

import requests.exceptions
import time_machine
from django.test import TestCase
from django.urls import reverse


class JokeAPITestCase(TestCase):
    def setUp(self):
        self.url = reverse("joke")
        self.mock_joke = {
            "type": "general",
            "setup": "Well...",
            "punchline": "That’s a deep subject.",
            "id": 64,
        }

    @patch("game.views.requests.get")
    def test_get_joke_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_joke
        mock_response.raise_for_status.return_value = None

        mock_get.return_value = mock_response

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.mock_joke)

    @patch("game.views.requests.get")
    def test_get_joke_fail(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 server error"
        )

        mock_get.return_value = mock_response

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 500)
        self.assertIn("500 server error", response.json()["error"])

    @patch("game.views.requests.get")
    def test_get_joke_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("504 timeout error")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json(), {"error": "timeout"})

    @time_machine.travel("15:00")
    @patch("game.views.requests.get")
    def test_get_joke_day(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_joke

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("setup", response.json())
        self.assertEqual(response.json()["type"], "general")

    @time_machine.travel("23:00")
    @patch("game.views.requests.get")
    def test_get_joke_night(self, mock_get):
        mock_get.return_value.status_code = 403
        mock_get.return_value.json.return_value = {
            "error": "you should have been sleeping now, come back tomorrow"
        }

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())

    @patch("game.views.requests.get")
    def test_get_joke_day_6_times(self, mock_get):

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_joke

        times = ["06:00", "08:45", "11:30", "16:10", "18:47", "21:59"]

        for time in times:
            with time_machine.travel(time):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                self.assertIn(response.json()["type"], "general")

        self.assertEqual(mock_get.call_count, 6)

    @patch("game.views.requests.get")
    def test_get_joke_night_6_times(self, mock_get):
        times = ["22:00", "00:02", "04:57", "03:33", "05:58", "05:59"]

        for time in times:
            with time_machine.travel(time):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 403)
                self.assertIn("error", response.json())

        mock_get.assert_not_called()
