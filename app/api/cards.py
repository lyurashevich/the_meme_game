from typing import List

from db import get_db
from fastapi import APIRouter, Depends, Path
from schemas.cards import (MemeCardCreate, MemeCardSchema, MemeCardUpdate,
                           SituationCardCreate, SituationCardSchema,
                           SituationCardUpdate)
from services.card_service import CardService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/cards", tags=["cards"])


# MemeCard endpoints
@router.get("/meme_cards", response_model=List[MemeCardSchema])
async def get_meme_cards(db: AsyncSession = Depends(get_db)):
    """Get all meme cards"""
    service = CardService(db)
    return await service.get_meme_cards()


@router.get("/meme_cards/{card_id}", response_model=MemeCardSchema)
async def get_meme_card(
    card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)
):
    """Get a specific meme card by ID"""
    service = CardService(db)
    return await service.get_meme_card(card_id)


@router.post("/meme_cards", response_model=MemeCardSchema, status_code=201)
async def create_meme_card(
    meme_card: MemeCardCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new meme card"""
    service = CardService(db)
    return await service.create_meme_card(meme_card)


@router.patch("/meme_cards/{card_id}", response_model=MemeCardSchema)
async def update_meme_card(
    card_id: int = Path(..., gt=0),
    meme_card: MemeCardUpdate = None,
    db: AsyncSession = Depends(get_db),
):
    """Update a meme card"""
    service = CardService(db)
    return await service.update_meme_card(card_id, meme_card)


@router.delete("/meme_cards/{card_id}", status_code=204)
async def delete_meme_card(
    card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)
):
    """Delete a meme card"""
    service = CardService(db)
    await service.delete_meme_card(card_id)


# SituationCard endpoints
@router.get("/situation_cards", response_model=List[SituationCardSchema])
async def get_situation_cards(db: AsyncSession = Depends(get_db)):
    """Get all situation cards"""
    service = CardService(db)
    return await service.get_situation_cards()


@router.get("/situation_cards/{card_id}", response_model=SituationCardSchema)
async def get_situation_card(
    card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)
):
    """Get a specific situation card by ID"""
    service = CardService(db)
    return await service.get_situation_card(card_id)


@router.post("/situation_cards", response_model=SituationCardSchema, status_code=201)
async def create_situation_card(
    situation_card: SituationCardCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new situation card"""
    service = CardService(db)
    return await service.create_situation_card(situation_card)


@router.patch("/situation_cards/{card_id}", response_model=SituationCardSchema)
async def update_situation_card(
    card_id: int = Path(..., gt=0),
    situation_card: SituationCardUpdate = None,
    db: AsyncSession = Depends(get_db),
):
    """Update a situation card"""
    service = CardService(db)
    return await service.update_situation_card(card_id, situation_card)


@router.delete("/situation_cards/{card_id}", status_code=204)
async def delete_situation_card(
    card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)
):
    """Delete a situation card"""
    service = CardService(db)
    await service.delete_situation_card(card_id)
