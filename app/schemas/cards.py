from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Where the picture is among the media files: path parts of letters, digits and "._-", separated by
# "/", e.g. "memes/3f9a1c.jpg". No part may start with a dot, so "../" can't lead out of the folder.
IMAGE_KEY_PATTERN = r"^[A-Za-z0-9_-][A-Za-z0-9._-]*(/[A-Za-z0-9_-][A-Za-z0-9._-]*)*$"
ImageKey = Field(..., min_length=1, max_length=255, pattern=IMAGE_KEY_PATTERN, examples=["memes/3f9a1c.jpg"])


class MemeCardCreate(BaseModel):
    image_key: str = ImageKey


class MemeCardUpdate(BaseModel):
    image_key: Optional[str] = Field(None, min_length=1, max_length=255, pattern=IMAGE_KEY_PATTERN)


class MemeCardSchema(BaseModel):
    id: int
    image_key: str
    # Built from the key and MEDIA_BASE_URL; what the browser loads
    image_url: str

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
