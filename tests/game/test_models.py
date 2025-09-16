import pytest
from sqlalchemy import select

from app.models import MemeCard, SituationCard
from tests.conftest import db_session


class TestCardModels:
    def test_meme_card_creation(self, db_session):
        card = MemeCard(image_url="https://example.com/meme.jpg")
        db_session.add(card)
        db_session.commit()

        cards = db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 1
        assert card.id is not None
        assert card.image_url == "https://example.com/meme.jpg"

    def test_delete_meme_card(self, db_session):
        card = MemeCard(image_url="https://example.com/meme.jpg")
        db_session.add(card)
        db_session.commit()

        db_session.delete(card)
        db_session.commit()

        cards = db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 0
        assert db_session.get(MemeCard, 1) is None

    def test_meme_card_update(self, db_session):
        card = MemeCard(image_url="https://example.com/meme.jpg")
        db_session.add(card)
        db_session.commit()

        card.image_url = "https://example.com/meme2.jpg"
        db_session.commit()
        db_session.refresh(card)

        assert card.image_url == "https://example.com/meme2.jpg"
        cards = db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 1
        assert card.id is not None
        assert card.image_url == "https://example.com/meme2.jpg"


class TestSituationCardModels:
    def test_situation_card_creation(self, db_session):
        card = SituationCard(id=1, text="Test situation")
        db_session.add(card)
        db_session.commit()

        assert card.id == 1
        assert card.text == "Test situation"

    @pytest.mark.parametrize(
        "text",
        [
            "Short situation",
            "Very long situation text that describes a complex scenario that players need to respond to with their meme cards",
            "Situation with special characters: !@#$%^&*()",
        ],
    )
    def test_situation_card_variations(self, db_session, text):
        card = SituationCard(text=text)
        db_session.add(card)
        db_session.commit()

        card_id = card.id

        assert card.id == card_id
        assert card.text == text

    def test_delete_situation_card(self, db_session):
        card = SituationCard(text="Test situation")
        db_session.add(card)
        db_session.commit()

        db_session.delete(card)
        db_session.commit()

        cards = db_session.execute(select(SituationCard))
        assert len(cards.scalars().all()) == 0
        assert db_session.get(SituationCard, 1) is None

    def test_situation_card_update(self, db_session):
        card = SituationCard(text="Test situation")
        db_session.add(card)
        db_session.commit()

        card.text = "Test situation 2"
        db_session.commit()
        db_session.refresh(card)

        assert card.text == "Test situation 2"
        cards = db_session.execute(select(SituationCard))
        assert len(cards.scalars().all()) == 1
        assert card.id is not None
        assert card.text == "Test situation 2"
