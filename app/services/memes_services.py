from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.models import MemeCard
from app.schemas.cards import MemeCardCreate, MemeCardUpdate


class CardService:
    MEME_CARDS: list[MemeCard] = []

    def __init__(self, db: Session):
        self.db = db

        if not self.MEME_CARDS:
            self.MEME_CARDS = self.get_meme_cards()

    def get_meme_cards(self) -> list[MemeCard]:
        result = self.db.execute(select(MemeCard))
        return result.scalars().all()

    def get_meme_card(self, card_id: int) -> MemeCard:
        result = self.db.execute(select(MemeCard).where(MemeCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meme card not found")
        return card

    def create_meme_card(self, card_data: MemeCardCreate) -> MemeCard:
        try:
            card = MemeCard(image_url=str(card_data.image_url))
            self.db.add(card)
            self.db.commit()
            self.db.refresh(card)
            return card
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create meme card",
            )

    def update_meme_card(self, card_id: int, card_data: MemeCardUpdate) -> MemeCard:
        card = self.get_meme_card(card_id)

        if card_data.image_url is not None:
            card.image_url = str(card_data.image_url)

        self.db.commit()
        self.db.refresh(card)
        return card

    def delete_meme_card(self, card_id: int) -> None:
        card = self.get_meme_card(card_id)
        self.db.delete(card)
        self.db.commit()
