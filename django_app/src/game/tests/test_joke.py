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
        self.night_response = {
            "error": "you should have been sleeping now, come back tomorrow"
        }

    def setup_day_mock(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_joke

    def setup_night_mock(self, mock_get):
        mock_get.return_value.status_code = 403
        mock_get.return_value.json.return_value = self.night_response

    def assert_successful_response(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.mock_joke)

    def assert_night_response(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), self.night_response)

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
    def test_get_joke_at_15_00(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("06:00")
    @patch("game.views.requests.get")
    def test_get_joke_at_06_00(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("08:45")
    @patch("game.views.requests.get")
    def test_get_joke_at_08_45(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("11:30")
    @patch("game.views.requests.get")
    def test_get_joke_at_11_30(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("16:10")
    @patch("game.views.requests.get")
    def test_get_joke_at_16_10(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("21:59")
    @patch("game.views.requests.get")
    def test_get_joke_21_59(self, mock_get):
        self.setup_day_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_successful_response(response)

    @time_machine.travel("22:00")
    @patch("game.views.requests.get")
    def test_get_joke_at_22_00(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("23:30")
    @patch("game.views.requests.get")
    def test_get_joke_at_23_30(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("04:59")
    @patch("game.views.requests.get")
    def test_get_joke_at_04_59(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("03:33")
    @patch("game.views.requests.get")
    def test_get_joke_at_03_33(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("02:22")
    @patch("game.views.requests.get")
    def test_get_joke_at_02_22(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("01:15")
    @patch("game.views.requests.get")
    def test_get_joke_at_01_15(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)

    @time_machine.travel("05:59")
    @patch("game.views.requests.get")
    def test_get_joke_at_05_59(self, mock_get):
        self.setup_night_mock(mock_get)

        response = self.client.get(self.url)
        self.assert_night_response(response)
