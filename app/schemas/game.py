from pydantic import BaseModel, ConfigDict


class StartGameRequest(BaseModel):
    room_id: str


class GameResponse(BaseModel):
    id: str
    room_id: str
    # state: str
    leader_index: int
    players: list[str]
    meme_deck_count: int
    situation_deck_count: int

    model_config = ConfigDict(from_attributes=True)


class StartGameResponse(BaseModel):
    status: str
    game: GameResponse


class SelectWinnerRequest(BaseModel):
    card_id: int


class SelectPlayerCardRequest(BaseModel):
    player_id: str
    card_id: int
