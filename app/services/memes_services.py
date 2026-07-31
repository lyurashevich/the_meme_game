from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import MemeCard
from app.schemas.cards import MemeCardCreate, MemeCardUpdate


class CardService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_meme_cards(self) -> list[MemeCard]:
        result = await self.db.execute(select(MemeCard))
        return result.scalars().all()

    async def get_meme_card(self, card_id: int) -> MemeCard:
        result = await self.db.execute(select(MemeCard).where(MemeCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meme card not found")
        return card

    async def create_meme_card(self, card_data: MemeCardCreate) -> MemeCard:
        try:
            card = MemeCard(image_url=str(card_data.image_url))
            self.db.add(card)
            await self.db.commit()
            await self.db.refresh(card)
            return card
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create meme card",
            )

    async def update_meme_card(self, card_id: int, card_data: MemeCardUpdate) -> MemeCard:
        card = await self.get_meme_card(card_id)

        if card_data.image_url is not None:
            card.image_url = str(card_data.image_url)

        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def delete_meme_card(self, card_id: int) -> None:
        card = await self.get_meme_card(card_id)
        await self.db.delete(card)
        await self.db.commit()
