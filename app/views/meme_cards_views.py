from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import require_admin
from app.schemas.cards import MemeCardCreate, MemeCardSchema, MemeCardUpdate
from app.services.memes_services import CardService

router = APIRouter(prefix="/api/memes", tags=["memes"])


@router.get("/", response_model=list[MemeCardSchema])
async def get_meme_cards(db: AsyncSession = Depends(get_db)):
    service = CardService(db)
    return await service.get_meme_cards()


@router.get("/{card_id}", response_model=MemeCardSchema)
async def get_meme_card(card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)):
    service = CardService(db)
    return await service.get_meme_card(card_id)


@router.post("/", response_model=MemeCardSchema, status_code=201, dependencies=[Depends(require_admin)])
async def create_meme_card(meme_card: MemeCardCreate, db: AsyncSession = Depends(get_db)):
    service = CardService(db)
    return await service.create_meme_card(meme_card)


@router.patch("/{card_id}", response_model=MemeCardSchema, dependencies=[Depends(require_admin)])
async def update_meme_card(
    meme_card: MemeCardUpdate,
    card_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    service = CardService(db)
    return await service.update_meme_card(card_id, meme_card)


@router.delete("/{card_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_meme_card(card_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db)):
    service = CardService(db)
    await service.delete_meme_card(card_id)
