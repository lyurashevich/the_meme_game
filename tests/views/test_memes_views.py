import pytest
from sqlalchemy import select

from app.models import MemeCard


class TestMemesViews:
    url = "/api/memes"

    async def test_get_situation_cards_view(self, client, db_session):
        cards = [MemeCard(image_key=f"memes/{i}.jpg") for i in range(3)]
        db_session.add_all(cards)
        await db_session.commit()

        response = await client.get(self.url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_get_situation_card(self, client, db_session):
        card = MemeCard(image_key="memes/1.jpg")
        db_session.add(card)
        await db_session.commit()

        response = await client.get(f"{self.url}/{card.id}")

        assert response.status_code == 200
        assert response.json() == {"id": card.id, "image_key": "memes/1.jpg", "image_url": "/media/memes/1.jpg"}

    async def test_cards_loaded_with_whole_addresses_can_be_read(self, client, db_session):
        # before: GET /api/memes/ failed with 500 on addresses that weren't http(s)
        db_session.add(MemeCard(image_key="http://localhost:5173/memes/a%20b.jpg"))
        await db_session.commit()

        response = await client.get(self.url)

        assert response.status_code == 200
        assert response.json()[0]["image_url"] == "http://localhost:5173/memes/a%20b.jpg"

    async def test_get_situation_card_view__not_found(self, client, db_session):
        response = await client.get(f"{self.url}/999")

        assert response.status_code == 404

    async def test_create_situation_card_view(self, client, admin_headers, db_session):
        response = await client.post(self.url, json={"image_key": "memes/1.jpg"}, headers=admin_headers)

        result = await db_session.execute(select(MemeCard).where(MemeCard.image_key == "memes/1.jpg"))
        card = result.scalar_one()

        assert response.status_code == 201
        assert response.json() == {"id": card.id, "image_key": "memes/1.jpg", "image_url": "/media/memes/1.jpg"}

    async def test_create__the_same_picture_twice(self, client, admin_headers, db_session):
        db_session.add(MemeCard(image_key="memes/1.jpg"))
        await db_session.commit()

        response = await client.post(self.url, json={"image_key": "memes/1.jpg"}, headers=admin_headers)

        assert response.status_code == 409

    @pytest.mark.parametrize(
        "image_key",
        ["", "../secret.jpg", "memes/../../etc/passwd", "/memes/1.jpg", "memes//1.jpg", "мем.jpg", "a b.jpg"],
    )
    async def test_create__bad_key(self, client, admin_headers, db_session, image_key):
        response = await client.post(self.url, json={"image_key": image_key}, headers=admin_headers)

        assert response.status_code == 422

    async def test_update_situation_card_view(self, client, admin_headers, db_session):

        card = MemeCard(image_key="memes/1.jpg")
        db_session.add(card)
        await db_session.commit()

        response = await client.patch(f"{self.url}/{card.id}", json={"image_key": "memes/2.jpg"}, headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == {"id": card.id, "image_key": "memes/2.jpg", "image_url": "/media/memes/2.jpg"}

    async def test_update__to_a_picture_another_card_has(self, client, admin_headers, db_session):
        card = MemeCard(image_key="memes/1.jpg")
        db_session.add_all([card, MemeCard(image_key="memes/2.jpg")])
        await db_session.commit()

        response = await client.patch(f"{self.url}/{card.id}", json={"image_key": "memes/2.jpg"}, headers=admin_headers)

        assert response.status_code == 409

    async def test_update_situation_card_view__not_found(self, client, admin_headers, db_session):

        response = await client.patch(f"{self.url}/999", json={"image_key": "memes/1.jpg"}, headers=admin_headers)

        assert response.status_code == 404

    async def test_delete_situation_card_view(self, client, admin_headers, db_session):
        card = MemeCard(image_key="http://memes.org/1")
        db_session.add(card)
        await db_session.commit()

        response = await client.delete(f"{self.url}/{card.id}", headers=admin_headers)

        assert response.status_code == 204
        result = await db_session.execute(select(MemeCard).where(MemeCard.id == card.id))
        assert not result.scalar_one_or_none()

    async def test_delete_situation_card_view__not_found(self, client, admin_headers, db_session):
        response = await client.delete(f"{self.url}/999", headers=admin_headers)

        assert response.status_code == 404
