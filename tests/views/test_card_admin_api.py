"""Changing the card database needs the admin token; reading it doesn't.

Before: anyone who found the server could create, change or delete every card with a plain
HTTP request - e.g. delete all memes, after which no game could start.
"""

import pytest
from sqlalchemy import select

from app.config import Settings, get_settings
from app.main import app
from app.models import MemeCard, SituationCard
from tests.helpers import TEST_ADMIN_TOKEN

WRITE_REQUESTS = [
    ("post", "/api/memes/", {"image_url": "http://memes.org/new"}),
    ("patch", "/api/memes/{meme_id}", {"image_url": "http://memes.org/changed"}),
    ("delete", "/api/memes/{meme_id}", None),
    ("post", "/api/situations/", {"text": "new situation"}),
    ("patch", "/api/situations/{situation_id}", {"text": "changed situation"}),
    ("delete", "/api/situations/{situation_id}", None),
]


@pytest.fixture
async def cards(db_session):
    meme = MemeCard(image_url="http://memes.org/original")
    situation = SituationCard(text="original situation")
    db_session.add_all([meme, situation])
    await db_session.commit()
    return {"meme_id": meme.id, "situation_id": situation.id}


@pytest.fixture
def server_admin_token():
    """Configure the server's ADMIN_TOKEN for the test (None or "" = not configured)."""

    def configure(token):
        app.dependency_overrides[get_settings] = lambda: Settings(admin_token=token)

    yield configure
    app.dependency_overrides.pop(get_settings, None)


async def send(client, method, url, body, cards, headers=None):
    kwargs = {"headers": headers or {}}
    if body is not None:
        kwargs["json"] = body
    return await getattr(client, method)(url.format(**cards), **kwargs)


async def card_database(db_session):
    db_session.expire_all()
    memes = (await db_session.execute(select(MemeCard.image_url))).scalars().all()
    situations = (await db_session.execute(select(SituationCard.text))).scalars().all()
    return sorted(memes), sorted(situations)


UNCHANGED = (["http://memes.org/original"], ["original situation"])


@pytest.mark.parametrize("method, url, body", WRITE_REQUESTS)
class TestWriteEndpoints:
    @pytest.mark.parametrize("configured", [None, ""])
    async def test_disabled_when_no_admin_token_is_configured(
        self, client, db_session, cards, server_admin_token, method, url, body, configured
    ):
        server_admin_token(configured)

        response = await send(client, method, url, body, cards, headers={"X-Admin-Token": "anything"})

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "admin_api_disabled"
        assert await card_database(db_session) == UNCHANGED

    @pytest.mark.parametrize("headers", [{}, {"X-Admin-Token": "wrong"}, {"X-Admin-Token": ""}])
    async def test_rejected_without_the_right_token(
        self, client, db_session, cards, server_admin_token, method, url, body, headers
    ):
        server_admin_token(TEST_ADMIN_TOKEN)

        response = await send(client, method, url, body, cards, headers=headers)

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_admin_token"
        assert await card_database(db_session) == UNCHANGED

    async def test_allowed_with_the_right_token(self, client, db_session, cards, admin_headers, method, url, body):
        response = await send(client, method, url, body, cards, headers=admin_headers)

        assert response.status_code in (200, 201, 204)
        assert await card_database(db_session) != UNCHANGED


class TestReadEndpoints:
    @pytest.mark.parametrize(
        "url", ["/api/memes/", "/api/memes/{meme_id}", "/api/situations/", "/api/situations/{situation_id}"]
    )
    async def test_open_without_a_token(self, client, cards, server_admin_token, url):
        server_admin_token(TEST_ADMIN_TOKEN)

        response = await client.get(url.format(**cards))

        assert response.status_code == 200


def test_swagger_offers_the_admin_token_on_write_endpoints_only():
    schema = app.openapi()
    assert schema["components"]["securitySchemes"]["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-Admin-Token",
    }

    secured = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if operation.get("security")
    }
    assert secured == {
        ("POST", "/api/memes/"),
        ("PATCH", "/api/memes/{card_id}"),
        ("DELETE", "/api/memes/{card_id}"),
        ("POST", "/api/situations/"),
        ("PATCH", "/api/situations/{card_id}"),
        ("DELETE", "/api/situations/{card_id}"),
    }
