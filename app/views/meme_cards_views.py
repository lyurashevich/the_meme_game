from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.cards import MemeCardCreate, MemeCardSchema, MemeCardUpdate
from app.services.memes_services import CardService

router = APIRouter(prefix="/memes", tags=["memes"])


@router.get("/", response_model=list[MemeCardSchema])
def get_meme_cards(db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_meme_cards()


@router.get("/{card_id}", response_model=MemeCardSchema)
def get_meme_card(card_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_meme_card(card_id)


@router.post("/", response_model=MemeCardSchema, status_code=201)
def create_meme_card(meme_card: MemeCardCreate, db: Session = Depends(get_db)):
    service = CardService(db)
    return service.create_meme_card(meme_card)


@router.patch("/{card_id}", response_model=MemeCardSchema)
def update_meme_card(
    meme_card: MemeCardUpdate,
    card_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    service = CardService(db)
    return service.update_meme_card(card_id, meme_card)


@router.delete("/{card_id}", status_code=204)
def delete_meme_card(card_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    service = CardService(db)
    service.delete_meme_card(card_id)
