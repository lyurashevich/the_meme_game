from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class MemeCardBase(BaseModel):
    image_url: HttpUrl


class MemeCardCreate(MemeCardBase):
    pass


class MemeCardUpdate(BaseModel):
    image_url: Optional[HttpUrl] = None


class MemeCardSchema(MemeCardBase):
    id: int

    class Config:
        from_attributes = True


class SituationCardBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class SituationCardCreate(SituationCardBase):
    pass


class SituationCardUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=500)


class SituationCardSchema(SituationCardBase):
    id: int

    class Config:
        from_attributes = True
