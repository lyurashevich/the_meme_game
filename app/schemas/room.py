from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RoomCreateSchema(BaseModel):
    player_id: str
    name: str | None = None
    max_players: int = 10
    is_private: bool = False

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RoomResponseSchema(BaseModel):
    id: str
    name: str
    max_players: int
    is_private: bool
    owner_id: str
    players_count: int
    invitation_link: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoomStateSchema(BaseModel):
    name: str
    max_players: int
    is_private: bool
    players_count: int

    model_config = ConfigDict(from_attributes=True)


class JoinRoomSchema(BaseModel):
    player_id: str
    room_id: str
    confirm: bool = False


class LeaveRoomSchema(BaseModel):
    player_id: str
    confirm: bool = False


class LeaveRoomResponseSchema(BaseModel):
    requires_confirmation: bool
