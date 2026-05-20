from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import SituationCard
from app.schemas.cards import SituationCardCreate, SituationCardUpdate


class CardService:

    def __init__(self, db: Session):
        self.db = db

    def get_situation_cards(self) -> list[SituationCard]:
        result = self.db.execute(select(SituationCard))
        return result.scalars().all()

    def get_situation_card(self, card_id: int) -> SituationCard:
        result = self.db.execute(select(SituationCard).where(SituationCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Situation card not found")
        return card

    def create_situation_card(self, card_data: SituationCardCreate) -> SituationCard:
        try:
            card = SituationCard(text=card_data.text)
            self.db.add(card)
            self.db.commit()
            self.db.refresh(card)
            return card
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create situation card",
            )

    def update_situation_card(self, card_id: int, card_data: SituationCardUpdate) -> SituationCard:
        card = self.get_situation_card(card_id)

        if card_data.text is not None:
            card.text = card_data.text

        self.db.commit()
        self.db.refresh(card)
        return card

    def delete_situation_card(self, card_id: int) -> None:
        card = self.get_situation_card(card_id)
        self.db.delete(card)
        self.db.commit()
