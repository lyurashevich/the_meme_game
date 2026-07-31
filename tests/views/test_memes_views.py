from sqlalchemy import select

from app.models import MemeCard


class TestMemesViews:
    url = "/memes"

    async def test_get_situation_cards_view(self, client, db_session):
        cards = [MemeCard(image_url=f"http://memes.org/{i}") for i in range(3)]
        db_session.add_all(cards)
        await db_session.commit()

        response = await client.get(self.url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_get_situation_card(self, client, db_session):
        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        await db_session.commit()

        response = await client.get(f"{self.url}/{card.id}")

        assert response.status_code == 200
        assert response.json()["id"] == card.id
        assert response.json()["image_url"] == card.image_url

    async def test_get_situation_card_view__not_found(self, client, db_session):
        response = await client.get(f"{self.url}/999")

        assert response.status_code == 404

    async def test_create_situation_card_view(self, client, db_session):
        response = await client.post(self.url, json={"image_url": "http://memes.org/1"})

        result = await db_session.execute(select(MemeCard).where(MemeCard.image_url == "http://memes.org/1"))
        card = result.scalar_one()

        assert response.status_code == 201
        assert response.json()["id"] == card.id
        assert response.json()["image_url"] == card.image_url

    async def test_update_situation_card_view(self, client, db_session):

        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        await db_session.commit()

        response = await client.patch(f"{self.url}/{card.id}", json={"image_url": "http://memes.org/2"})

        assert response.status_code == 200
        assert response.json()["image_url"] == "http://memes.org/2"
        assert response.json()["id"] == card.id

    async def test_update_situation_card_view__not_found(self, client, db_session):

        response = await client.patch(f"{self.url}/999", json={"image_url": "http://memes.org/1"})

        assert response.status_code == 404

    async def test_delete_situation_card_view(self, client, db_session):
        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        await db_session.commit()

        response = await client.delete(f"{self.url}/{card.id}")

        assert response.status_code == 204
        result = await db_session.execute(select(MemeCard).where(MemeCard.id == card.id))
        assert not result.scalar_one_or_none()

    async def test_delete_situation_card_view__not_found(self, client, db_session):
        response = await client.delete(f"{self.url}/999")

        assert response.status_code == 404
