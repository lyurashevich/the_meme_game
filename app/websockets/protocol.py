"""Envelope of client -> server websocket messages and the ack/error replies to them."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.game.enums import WebsocketEvents


class ClientMessage(BaseModel):
    event: str
    request_id: str | None = None  # echoed back in the reply so the client can match it to the request
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionPayload(BaseModel):
    """Base class for action payloads; unknown fields are rejected to surface client bugs early."""

    model_config = ConfigDict(extra="forbid")


class EmptyPayload(ActionPayload):
    pass


def build_ack(request_id: str | None, payload: dict | None = None) -> dict:
    return {"event": WebsocketEvents.ACK.value, "request_id": request_id, "payload": payload or {}}


def build_error(request_id: str | None, code: str, message: str, details: list | None = None) -> dict:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details

    return {"event": WebsocketEvents.ERROR.value, "request_id": request_id, "payload": payload}
