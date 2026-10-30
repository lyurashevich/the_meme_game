from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_ROUND_TIME_LIMITS = (60, 90, 120)


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
