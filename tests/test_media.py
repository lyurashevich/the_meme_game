"""The address a meme picture is loaded from: MEDIA_BASE_URL plus the card's image key."""

import pytest

from app.config import Settings
from app.media import media_url


@pytest.mark.parametrize(
    "base_url, expected",
    [
        ("/media", "/media/memes/a.jpg"),
        ("/media/", "/media/memes/a.jpg"),  # no double slash
        ("https://cdn.example.com/memes-game", "https://cdn.example.com/memes-game/memes/a.jpg"),
    ],
)
def test_the_key_is_added_to_the_base_address(base_url, expected):
    assert media_url("memes/a.jpg", base_url) == expected


def test_unsafe_characters_in_the_key_are_encoded():
    assert media_url("memes/кот мем.jpg", "/media") == "/media/memes/%D0%BA%D0%BE%D1%82%20%D0%BC%D0%B5%D0%BC.jpg"


@pytest.mark.parametrize(
    "whole_address",
    ["http://localhost:5173/memes/a%20b.jpg", "https://memes.org/1", "/memes/a.jpg"],
)
def test_cards_loaded_with_whole_addresses_keep_them(whole_address):
    # cards loaded before there were keys: the column holds their whole address
    assert media_url(whole_address, "/media") == whole_address


def test_the_base_address_comes_from_the_settings(monkeypatch):
    monkeypatch.setattr("app.media.get_settings", lambda: Settings(media_base_url="https://cdn.example.com"))

    assert media_url("memes/a.jpg") == "https://cdn.example.com/memes/a.jpg"


def test_by_default_pictures_come_from_the_same_site(monkeypatch):
    monkeypatch.delenv("MEDIA_BASE_URL", raising=False)

    assert Settings(_env_file=None).media_base_url == "/media"
