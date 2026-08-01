from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_ROUND_TIME_LIMITS = (60, 90, 120)


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


class GameScore(BaseModel):
    id: str
    username: str
    score: int


class GameSettingsSchema(BaseModel):
    round_time_limit: int
    max_rounds: int | None = None
    score_to_win: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("round_time_limit")
    @classmethod
    def check_round_time_limit(cls, value: int) -> int:
        if value not in ALLOWED_ROUND_TIME_LIMITS:
            raise ValueError(f"Round time limit must be one of {ALLOWED_ROUND_TIME_LIMITS}")
        return value

    @field_validator("max_rounds", "score_to_win")
    @classmethod
    def check_positive(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("Value must be positive")
        return value


class UpdateGameSettingsRequest(BaseModel):
    player_id: str
    settings: GameSettingsSchema


class EndGameRequest(BaseModel):
    player_id: str
