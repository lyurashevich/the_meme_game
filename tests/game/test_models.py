import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import MemeCard, SituationCard


class TestCardModels:
    async def test_meme_card_creation(self, db_session):
        card = MemeCard(image_key="memes/meme.jpg")
        db_session.add(card)
        await db_session.commit()

        cards = await db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 1
        assert card.id is not None
        assert card.image_key == "memes/meme.jpg"

    async def test_delete_meme_card(self, db_session):
        card = MemeCard(image_key="memes/meme.jpg")
        db_session.add(card)
        await db_session.commit()

        await db_session.delete(card)
        await db_session.commit()

        cards = await db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 0
        assert await db_session.get(MemeCard, 1) is None

    async def test_meme_card_update(self, db_session):
        card = MemeCard(image_key="memes/meme.jpg")
        db_session.add(card)
        await db_session.commit()

        card.image_key = "memes/meme2.jpg"
        await db_session.commit()
        await db_session.refresh(card)

        assert card.image_key == "memes/meme2.jpg"
        cards = await db_session.execute(select(MemeCard))
        assert len(cards.scalars().all()) == 1

    async def test_the_same_picture_cant_be_added_twice(self, db_session):
        db_session.add_all([MemeCard(image_key="memes/meme.jpg"), MemeCard(image_key="memes/meme.jpg")])

        with pytest.raises(IntegrityError):
            await db_session.commit()

    def test_image_url_is_the_media_address_plus_the_key(self):
        assert MemeCard(image_key="memes/meme.jpg").image_url == "/media/memes/meme.jpg"


class TestSituationCardModels:
    async def test_situation_card_creation(self, db_session):
        card = SituationCard(id=1, text="Test situation")
        db_session.add(card)
        await db_session.commit()

        assert card.id == 1
        assert card.text == "Test situation"

    @pytest.mark.parametrize(
        "text",
        [
            "Short situation",
            "Very long situation text that describes a complex scenario that players need to respond to with "
            "their meme cards",
            "Situation with special characters: !@#$%^&*()",
        ],
    )
    async def test_situation_card_variations(self, db_session, text):
        card = SituationCard(text=text)
        db_session.add(card)
        await db_session.commit()

        card_id = card.id

        assert card.id == card_id
        assert card.text == text

    async def test_delete_situation_card(self, db_session):
        card = SituationCard(text="Test situation")
        db_session.add(card)
        await db_session.commit()

        await db_session.delete(card)
        await db_session.commit()

        cards = await db_session.execute(select(SituationCard))
        assert len(cards.scalars().all()) == 0
        assert await db_session.get(SituationCard, 1) is None

    async def test_situation_card_update(self, db_session):
        card = SituationCard(text="Test situation")
        db_session.add(card)
        await db_session.commit()

        card.text = "Test situation 2"
        await db_session.commit()
        await db_session.refresh(card)

        assert card.text == "Test situation 2"
        cards = await db_session.execute(select(SituationCard))
        assert len(cards.scalars().all()) == 1
        assert card.id is not None
        assert card.text == "Test situation 2"
