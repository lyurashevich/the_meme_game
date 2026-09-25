from pydantic import BaseModel


class BasePlayerProfileSchema(BaseModel):
    username: str | None = ''
    avatar_id: str | None = None


class BasePlayerProfileResponseSchema(BasePlayerProfileSchema):
    id: str
    is_connected: bool
