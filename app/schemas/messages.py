from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChetMessageSchema(BaseModel):
    player_id: str
    room_id: str
    message: str
    timestamp: Optional[datetime] = None


class ChatMessageResponse(BaseModel):
    event: str = "chat_message"
    player_id: str
    player_name: str
    message: str
    timestamp: str
    room_id: str
