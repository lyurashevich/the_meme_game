from sqlalchemy import select

from app.models import MemeCard
from tests.conftest import client


class TestMemesViews:
    url = "/memes"

    def test_get_situation_cards_view(self, client, db_session):
        cards = [MemeCard(image_url=f"http://memes.org/{i}") for i in range(3)]
        db_session.add_all(cards)
        db_session.commit()

        response = client.get(self.url)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_get_situation_card(self, client, db_session):
        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        db_session.commit()

        response = client.get(f"{self.url}/{card.id}")

        assert response.status_code == 200
        assert response.json()["id"] == card.id
        assert response.json()["image_url"] == card.image_url

    def test_get_situation_card_view__not_found(self, client, db_session):
        response = client.get(f"{self.url}/999")

        assert response.status_code == 404

    def test_create_situation_card_view(self, client, db_session):
        response = client.post(self.url, json={"image_url": "http://memes.org/1"})

        card = db_session.execute(select(MemeCard).where(MemeCard.image_url == "http://memes.org/1")).scalar_one()

        assert response.status_code == 201
        assert response.json()["id"] == card.id
        assert response.json()["image_url"] == card.image_url

    def test_update_situation_card_view(self, client, db_session):

        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        db_session.commit()

        response = client.patch(f"{self.url}/{card.id}", json={"image_url": "http://memes.org/2"})

        assert response.status_code == 200
        assert response.json()["image_url"] == "http://memes.org/2"
        assert response.json()["id"] == card.id

    def test_update_situation_card_view__not_found(self, client, db_session):

        response = client.patch(f"{self.url}/999", json={"image_url": "http://memes.org/1"})

        assert response.status_code == 404

    def test_delete_situation_card_view(self, client, db_session):
        card = MemeCard(image_url="http://memes.org/1")
        db_session.add(card)
        db_session.commit()

        response = client.delete(f"{self.url}/{card.id}")

        assert response.status_code == 204
        assert not db_session.execute(select(MemeCard).where(MemeCard.id == card.id)).scalar_one_or_none()

    def test_delete_situation_card_view__not_found(self, client, db_session):
        response = client.delete(f"{self.url}/999")

        assert response.status_code == 404
