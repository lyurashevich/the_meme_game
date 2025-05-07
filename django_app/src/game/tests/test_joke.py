import requests.exceptions
import responses
import time_machine
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

NIGHT_TIMES = ["22:00", "23:30", "01:15", "02:22", "03:33", "05:59"]

DAY_TIMES = ["06:00", "07:23", "11:11", "15:36", "18:29", "21:59"]


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

    @parameterized.expand(NIGHT_TIMES)
    @responses.activate
    def test_get_joke_night(self, time):

        with time_machine.travel(time):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), self.night_response)
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

    @parameterized.expand(DAY_TIMES)
    @responses.activate
    def test_get_joke_day(self, time):
        self.setup_day_response()

        with time_machine.travel(time):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.mock_joke)
        self.assertEqual(len(responses.calls), 1)
