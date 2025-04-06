from unittest import TestCase

from rest_framework import status
from rest_framework.test import APIClient


class AnonymousTokenViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_request_returns_token(self):
        response = self.client.post("/api/token/anonymous_token/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIsInstance(response.data["access"], str)
        self.assertGreater(len(response.data["access"]), 0)
