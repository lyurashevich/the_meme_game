import requests.exceptions
import responses
import time_machine
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized


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

    def assert_successful_response(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.mock_joke)

    def assert_night_response(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), self.night_response)

    @responses.activate
    def test_get_joke_fail(self):
        responses.add(
            responses.GET,
            "https://official-joke-api.appspot.com/random_joke",
            status=500,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 500)

    @responses.activate
    def test_get_joke_timeout(self):
        responses.add(
            responses.GET,
            "https://official-joke-api.appspot.com/random_joke",
            body=requests.exceptions.Timeout("timeout"),
        )
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json(), {"error": "timeout"})

    @parameterized.expand(
        [
            ("22_00", "22:00"),
            ("23_30", "23:30"),
            ("01_15", "01:15"),
            ("02_22", "02:22"),
            ("03_33", "03:33"),
            ("05_59", "05:59"),
        ]
    )
    @responses.activate
    def test_get_joke_night(self, _, time):

        with time_machine.travel(time):
            response = self.client.get(self.url)

        self.assert_night_response(response)
        self.assertEqual(len(responses.calls), 0)

    @staticmethod
    def setup_day_response():
        responses.add(
            responses.GET,
            "https://official-joke-api.appspot.com/random_joke",
            json={
                "type": "general",
                "setup": "Well...",
                "punchline": "That’s a deep subject.",
                "id": 64,
            },
            status=200,
        )

    @parameterized.expand(
        [
            ("06_00", "06:00"),
            ("07_23", "07:23"),
            ("11_11", "11:11"),
            ("15_36", "15:36"),
            ("18_29", "18:29"),
            ("21_59", "21:59"),
        ]
    )
    @responses.activate
    def test_get_joke_day(self, _, time):
        self.setup_day_response()

        with time_machine.travel(time):
            response = self.client.get(self.url)

        self.assert_successful_response(response)
        self.assertEqual(len(responses.calls), 1)
