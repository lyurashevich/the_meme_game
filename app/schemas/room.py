from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RoomStateSchema(BaseModel):
    id: str
    name: str
    owner_name: str
    players_count: int
    max_players: int
    owner_id: str
    invitation_link: str | None = None
    rounds_count: int | None = None
    time_limit: int
    is_private: bool
    # status: str

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class LeaveRoomResponseSchema(BaseModel):
    requires_confirmation: bool
