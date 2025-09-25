from pydantic import BaseModel, ConfigDict


class PlayerChoiceSchema(BaseModel):
    player_id: str
    username: str
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class StartNewRoundRequestSchema(BaseModel):
    room_id: str


class StartNewRoundResponseSchema(BaseModel):
    game_id: str
    round_number: int
    leader_id: str
    situation_card_text: str
    # state: str
    time_limit: int

    model_config = ConfigDict(from_attributes=True)


class GameRoundInfoSchema(BaseModel):
    game_id: str
    round_number: int
    leader_id: str
    situation_card_id: int
    player_choices_list: list[PlayerChoiceSchema] | None = None
    # state: ...
    # todo: implement time left
    time_limit: int = 60  # seconds

    model_config = ConfigDict(from_attributes=True)


class EndRoundRequestSchema(BaseModel):
    round_number: int
    leader_id: int
    situation_card_id: int
    player_choices: dict[int, int]  # player_id -> selected_card
    winner_id: int
    # state: RoundState = RoundState.CHOOSING_CARDS
    # start_time: datetime
    # end_time: datetime
    time_limit: int = 60  # seconds


class EndRoundResponseSchema(BaseModel):
    pass
