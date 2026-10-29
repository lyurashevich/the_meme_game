from sqlalchemy import select

from app.models import SituationCard


class TestSituationViews:
    url = "/api/situations"

    async def test_get_situation_cards_view(self, client, db_session):
        cards = [SituationCard(text=f"situation {i}") for i in range(3)]
        db_session.add_all(cards)
        await db_session.commit()

        response = await client.get(self.url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_get_situation_card(self, client, db_session):
        card = SituationCard(text="Situation card")
        db_session.add(card)
        await db_session.commit()

        response = await client.get(f"{self.url}/{card.id}")

        assert response.status_code == 200
        assert response.json()["id"] == card.id
        assert response.json()["text"] == card.text

    async def test_get_situation_card_view__not_found(self, client, db_session):
        response = await client.get(f"{self.url}/999")

        assert response.status_code == 404

    async def test_create_situation_card_view(self, client, db_session):
        response = await client.post(self.url, json={"text": "Test situation"})

        result = await db_session.execute(select(SituationCard).where(SituationCard.text == "Test situation"))
        card = result.scalar_one()

        assert response.status_code == 201
        assert response.json()["id"] == card.id
        assert response.json()["text"] == card.text

    async def test_update_situation_card_view(self, client, db_session):

        card = SituationCard(text="Test situation")
        db_session.add(card)
        await db_session.commit()

        response = await client.patch(f"{self.url}/{card.id}", json={"text": "Test situation2"})

        assert response.status_code == 200
        assert response.json()["text"] == "Test situation2"
        assert response.json()["id"] == card.id

    async def test_update_situation_card_view__not_found(self, client, db_session):

        response = await client.patch(f"{self.url}/999", json={"text": "Test situation2"})

        assert response.status_code == 404

    async def test_delete_situation_card_view(self, client, db_session):
        card = SituationCard(text="situation to delete")
        db_session.add(card)
        await db_session.commit()

        response = await client.delete(f"{self.url}/{card.id}")

        assert response.status_code == 204
        result = await db_session.execute(select(SituationCard).where(SituationCard.id == card.id))
        assert not result.scalar_one_or_none()

    async def test_delete_situation_card_view__not_found(self, client, db_session):
        response = await client.delete(f"{self.url}/999")

        assert response.status_code == 404
