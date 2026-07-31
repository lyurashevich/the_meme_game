from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SituationCard
from app.schemas.cards import SituationCardCreate, SituationCardUpdate


class CardService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_situation_cards(self) -> list[SituationCard]:
        result = await self.db.execute(select(SituationCard))
        return result.scalars().all()

    async def get_situation_card(self, card_id: int) -> SituationCard:
        result = await self.db.execute(select(SituationCard).where(SituationCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Situation card not found")
        return card

    async def create_situation_card(self, card_data: SituationCardCreate) -> SituationCard:
        try:
            card = SituationCard(text=card_data.text)
            self.db.add(card)
            await self.db.commit()
            await self.db.refresh(card)
            return card
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create situation card",
            )

    async def update_situation_card(self, card_id: int, card_data: SituationCardUpdate) -> SituationCard:
        card = await self.get_situation_card(card_id)

        if card_data.text is not None:
            card.text = card_data.text

        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def delete_situation_card(self, card_id: int) -> None:
        card = await self.get_situation_card(card_id)
        await self.db.delete(card)
        await self.db.commit()
