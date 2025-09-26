from pydantic import BaseModel, ConfigDict


class PlayerCardsSchema(BaseModel):
    id: int
    image_url: str


class PlayerCreateSchema(BaseModel):
    username: str | None = None


class PlayerStateSchema(PlayerCreateSchema):
    handed_cards: list[int]  # cards' ids
    score: int

    model_config = ConfigDict(from_attributes=True)


class PlayerSchema(PlayerStateSchema):
    id: str
    is_host: bool
    is_connected: bool
    connection_order: int

    model_config = ConfigDict(from_attributes=True)
