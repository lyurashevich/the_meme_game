from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BasePlayerProfileSchema(BaseModel):
    username: str | None = ""
    avatar_id: str | None = None


class BasePlayerProfileResponseSchema(BasePlayerProfileSchema):
    id: str
    is_connected: bool

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)
