from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MemeCardBase(BaseModel):
    image_url: HttpUrl


class MemeCardsCreate(BaseModel):
    urls: List[HttpUrl]
    pass


class MemeCardUpdate(BaseModel):
    image_url: Optional[HttpUrl] = None


class MemeCardSchema(MemeCardBase):
    image_url: HttpUrl
    id: int

    model_config = ConfigDict(from_attributes=True)


class SituationCardBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class SituationCardCreate(SituationCardBase):
    pass


class SituationCardUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=500)


class SituationCardSchema(SituationCardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
