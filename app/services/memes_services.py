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
        card = MemeCard(image_key=card_data.image_key)
        self.db.add(card)
        await self._commit(card)
        return card

    async def update_meme_card(self, card_id: int, card_data: MemeCardUpdate) -> MemeCard:
        card = await self.get_meme_card(card_id)

        if card_data.image_key is not None:
            card.image_key = card_data.image_key

        await self._commit(card)
        return card

    async def _commit(self, card: MemeCard) -> None:
        try:
            await self.db.commit()
        except IntegrityError:  # the only constraint that can fail: image_key is unique
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A meme card with this image already exists",
            )
        await self.db.refresh(card)

    async def delete_meme_card(self, card_id: int) -> None:
        card = await self.get_meme_card(card_id)
        await self.db.delete(card)
        await self.db.commit()
