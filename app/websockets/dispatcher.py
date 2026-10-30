import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dependencies import Services
from app.exceptions import CustomException
from app.game.dataclasses import Player
from app.websockets.protocol import (
    ClientMessage,
    EmptyPayload,
    build_ack,
    build_error,
)

logger = logging.getLogger(__name__)


@dataclass
class ActionContext:
    """What a handler knows about the request: who sent it (taken from the connection) and the services."""

    player: Player
    services: Services
    session_factory: async_sessionmaker[AsyncSession]


ActionHandler = Callable[[ActionContext, Any], Awaitable[dict | None]]


class Dispatcher:
    """Routes client websocket messages to registered action handlers.

    Every message gets exactly one reply: ``ack`` with the handler's result, or
    ``error`` with a code. Handler errors never break the connection.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, tuple[type[BaseModel], ActionHandler]] = {}

    def action(
        self, event: str, payload_schema: type[BaseModel] = EmptyPayload
    ) -> Callable[[ActionHandler], ActionHandler]:
        def decorator(handler: ActionHandler) -> ActionHandler:
            if event in self._handlers:
                raise ValueError(f"Handler for event {event!r} is already registered")

            self._handlers[event] = (payload_schema, handler)
            return handler

        return decorator

    async def dispatch(self, ctx: ActionContext, raw_message: str) -> dict:
        try:
            message = ClientMessage.model_validate_json(raw_message)
        except ValidationError as e:
            return build_error(None, "invalid_message", "Message must be a JSON object with an event", _details(e))

        request_id = message.request_id

        entry = self._handlers.get(message.event)
        if entry is None:
            return build_error(request_id, "unknown_event", f"Unknown event: {message.event}")

        payload_schema, handler = entry

        try:
            payload = payload_schema.model_validate(message.payload)
        except ValidationError as e:
            return build_error(request_id, "validation_error", "Invalid payload", _details(e))

        try:
            result = await handler(ctx, payload)
        except CustomException as e:
            return build_error(request_id, e.code, e.message)
        except Exception:
            logger.exception("Unhandled error in %r handler for player %s", message.event, ctx.player.id)
            return build_error(request_id, "internal_error", "Internal server error")

        return build_ack(request_id, result)


def _details(error: ValidationError) -> list:
    # context and input may hold values that aren't JSON-serializable (or echo client data back)
    return error.errors(include_url=False, include_context=False, include_input=False)
