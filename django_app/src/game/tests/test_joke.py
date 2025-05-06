from unittest.mock import MagicMock, patch

import requests.exceptions
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

    @patch("game.views.is_daytime", return_value=True)
    @patch("game.views.requests.get")
    def test_get_joke_day(self, mock_get, mock_daytime):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_joke

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("setup", response.json())
        self.assertEqual(response.json()["type"], "general")

    @patch("game.views.is_daytime", return_value=False)
    @patch("game.views.requests.get")
    def test_get_joke_night(self, mock_get, mock_daytime):
        mock_get.return_value.status_code = 403
        mock_get.return_value.json.return_value = {
            "error": "you should have been sleeping now, come back tomorrow"
        }

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())
