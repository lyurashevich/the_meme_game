from typing import Annotated

from pydantic import StringConstraints

from app.exceptions import PlayerNotInRoomException
from app.websockets.dispatcher import ActionContext, Dispatcher
from app.websockets.protocol import ActionPayload

dispatcher = Dispatcher()


class ChatMessagePayload(ActionPayload):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


@dispatcher.action("chat_message", ChatMessagePayload)
async def chat_message(ctx: ActionContext, payload: ChatMessagePayload) -> None:
    if not ctx.player.room_id:
        raise PlayerNotInRoomException()

    recipients, message = await ctx.services.room_service.send_chat_message(
        room_id=ctx.player.room_id,
        player=ctx.player,
        message=payload.text,
    )
    await ctx.services.connection_manager.broadcast_to_players(recipients, message)
