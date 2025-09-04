from fastapi import HTTPException, status
from models import MemeCard, SituationCard
from schemas.cards import (MemeCardCreate, MemeCardUpdate, SituationCardCreate,
                           SituationCardUpdate)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class CardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # MemeCard methods
    async def get_meme_cards(self) -> list[MemeCard]:
        """Get all meme cards"""
        result = await self.db.execute(select(MemeCard))
        return result.scalars().all()

    async def get_meme_card(self, card_id: int) -> MemeCard:
        """Get a specific meme card by ID"""
        result = await self.db.execute(select(MemeCard).where(MemeCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meme card not found"
            )
        return card

    async def create_meme_card(self, card_data: MemeCardCreate) -> MemeCard:
        """Create a new meme card"""
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

    async def update_meme_card(
        self, card_id: int, card_data: MemeCardUpdate
    ) -> MemeCard:
        """Update a meme card"""
        card = await self.get_meme_card(card_id)

        if card_data.image_url is not None:
            card.image_url = str(card_data.image_url)

        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def delete_meme_card(self, card_id: int) -> None:
        """Delete a meme card"""
        card = await self.get_meme_card(card_id)
        await self.db.delete(card)
        await self.db.commit()

    # SituationCard methods
    async def get_situation_cards(self) -> list[SituationCard]:
        """Get all situation cards"""
        result = await self.db.execute(select(SituationCard))
        return result.scalars().all()

    async def get_situation_card(self, card_id: int) -> SituationCard:
        """Get a specific situation card by ID"""
        result = await self.db.execute(
            select(SituationCard).where(SituationCard.id == card_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Situation card not found"
            )
        return card

    async def create_situation_card(
        self, card_data: SituationCardCreate
    ) -> SituationCard:
        """Create a new situation card"""
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

    async def update_situation_card(
        self, card_id: int, card_data: SituationCardUpdate
    ) -> SituationCard:
        """Update a situation card"""
        card = await self.get_situation_card(card_id)

        if card_data.text is not None:
            card.text = card_data.text

        await self.db.commit()
        await self.db.refresh(card)
        return card

    async def delete_situation_card(self, card_id: int) -> None:
        """Delete a situation card"""
        card = await self.get_situation_card(card_id)
        await self.db.delete(card)
        await self.db.commit()
