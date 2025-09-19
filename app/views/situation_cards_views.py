from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.cards import (SituationCardCreate, SituationCardSchema,
                               SituationCardUpdate)
from app.services.situations_services import CardService

router = APIRouter(prefix="/situations", tags=["situations"])


@router.get("/", response_model=list[SituationCardSchema])
def get_situation_cards(db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_situation_cards()


@router.get("/{card_id}", response_model=SituationCardSchema)
def get_situation_card(card_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_situation_card(card_id)


@router.post("/", response_model=SituationCardSchema, status_code=201)
def create_situation_card(situation_card: SituationCardCreate, db: Session = Depends(get_db)):
    service = CardService(db)
    return service.create_situation_card(situation_card)


@router.patch("/{card_id}", response_model=SituationCardSchema)
def update_situation_card(
    card_id: int = Path(..., gt=0),
    situation_card: SituationCardUpdate = None,
    db: Session = Depends(get_db),
):
    service = CardService(db)
    return service.update_situation_card(card_id, situation_card)


@router.delete("/{card_id}", status_code=204)
async def delete_situation_card(card_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    service = CardService(db)
    service.delete_situation_card(card_id)
