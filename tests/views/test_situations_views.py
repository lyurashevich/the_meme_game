from sqlalchemy import select

from app.models import SituationCard
from tests.conftest import client


class TestSituationViews:
    url = "/situations"

    def test_get_situation_cards_view(self, client, db_session):
        cards = [SituationCard(text=f"situation {i}") for i in range(3)]
        db_session.add_all(cards)
        db_session.commit()

        response = client.get(self.url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_get_situation_card(self, client, db_session):
        card = SituationCard(text="Situation card")
        db_session.add(card)
        db_session.commit()

        response = client.get(f"{self.url}/{card.id}")

        assert response.status_code == 200
        assert response.json()["id"] == card.id
        assert response.json()["text"] == card.text

    def test_get_situation_card_view__not_found(self, client, db_session):
        response = client.get(f"{self.url}/999")

        assert response.status_code == 404

    def test_create_situation_card_view(self, client, db_session):
        response = client.post(self.url, json={"text": "Test situation"})

        card = db_session.execute(select(SituationCard).where(SituationCard.text == "Test situation")).scalar_one()

        assert response.status_code == 201
        assert response.json()["id"] == card.id
        assert response.json()["text"] == card.text

    def test_update_situation_card_view(self, client, db_session):

        card = SituationCard(text="Test situation")
        db_session.add(card)
        db_session.commit()

        response = client.patch(f"{self.url}/{card.id}", json={"text": "Test situation2"})

        assert response.status_code == 200
        assert response.json()["text"] == "Test situation2"
        assert response.json()["id"] == card.id

    def test_update_situation_card_view__not_found(self, client, db_session):

        response = client.patch(f"{self.url}/999", json={"text": "Test situation2"})

        assert response.status_code == 404

    def test_delete_situation_card_view(self, client, db_session):
        card = SituationCard(text="situation to delete")
        db_session.add(card)
        db_session.commit()

        response = client.delete(f"{self.url}/{card.id}")

        assert response.status_code == 204
        assert not db_session.execute(select(SituationCard).where(SituationCard.id == card.id)).scalar_one_or_none()

    def test_delete_situation_card_view__not_found(self, client, db_session):
        response = client.delete(f"{self.url}/999")

        assert response.status_code == 404
