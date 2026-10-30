from typing import Annotated

from pydantic import ConfigDict, Field, StringConstraints

from app.exceptions import PlayerNotInRoomException
from app.schemas.game import GameSettingsSchema
from app.schemas.players import BasePlayerProfileSchema
from app.websockets.dispatcher import ActionContext, Dispatcher
from app.websockets.protocol import ActionPayload

dispatcher = Dispatcher()

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


def _current_room_id(ctx: ActionContext) -> str:
    if not ctx.player.room_id:
        raise PlayerNotInRoomException()

    return ctx.player.room_id


# --- profile ---


class UpdateProfilePayload(ActionPayload):
    username: Username | None = None
    avatar_id: str | None = None


@dispatcher.action("update_profile", UpdateProfilePayload)
async def update_profile(ctx: ActionContext, payload: UpdateProfilePayload) -> dict:
    player = await ctx.services.player_service.update_player_profile(
        ctx.player.id, BasePlayerProfileSchema(username=payload.username, avatar_id=payload.avatar_id)
    )

    return {"username": player.username, "avatar_id": player.avatar_id}


# --- rooms ---


class CreateRoomPayload(ActionPayload):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)] | None = None
    max_players: int = Field(default=10, ge=3, le=10)


@dispatcher.action("create_room", CreateRoomPayload)
async def create_room(ctx: ActionContext, payload: CreateRoomPayload) -> dict:
    services = ctx.services
    services.game_manager.validate_player_can_join_room(ctx.player)

    room = await services.room_service.create_room(
        owner=ctx.player, room_name=payload.name, max_players=payload.max_players
    )

    # announce the new room to everyone who is browsing the room list
    players_in_rooms = {p.id for p in await services.player_service.get_players() if p.room_id}
    audience = list(set(services.connection_manager.player_sockets) - players_in_rooms)
    recipients, message = services.room_service.build_room_created_message(room, audience)
    await services.connection_manager.broadcast_to_players(recipients, message)

    return {"room_id": room.id}


class JoinRoomPayload(ActionPayload):
    room_id: str


@dispatcher.action("join_room", JoinRoomPayload)
async def join_room(ctx: ActionContext, payload: JoinRoomPayload) -> dict:
    services = ctx.services
    services.game_manager.validate_player_can_join_room(ctx.player)

    await services.room_service.join_room(payload.room_id, ctx.player)
    room = await services.room_service.get_room(payload.room_id)

    for recipients, message in services.room_service.build_join_room_messages(room, ctx.player):
        await services.connection_manager.broadcast_to_players(recipients, message)

    return {"room_id": room.id}


class LeaveRoomPayload(ActionPayload):
    confirm: bool = False


@dispatcher.action("leave_room", LeaveRoomPayload)
async def leave_room(ctx: ActionContext, payload: LeaveRoomPayload) -> dict:
    result = await ctx.services.game_service.process_leave(ctx.player, _current_room_id(ctx), payload.confirm)

    return result.model_dump()


class UpdateSettingsPayload(GameSettingsSchema):
    model_config = ConfigDict(extra="forbid")


@dispatcher.action("update_settings", UpdateSettingsPayload)
async def update_settings(ctx: ActionContext, payload: UpdateSettingsPayload) -> dict:
    settings = await ctx.services.game_service.change_game_settings(
        room_id=_current_room_id(ctx), player_id=ctx.player.id, data=payload
    )

    return GameSettingsSchema.model_validate(settings).model_dump()


# --- game ---


@dispatcher.action("start_game")
async def start_game(ctx: ActionContext, payload: ActionPayload) -> None:
    game_service = ctx.services.game_service

    async with ctx.session_factory() as db:
        game = await game_service.start_game(_current_room_id(ctx), ctx.player.id, db)

    for recipients, message in game_service.build_game_started_messages(game):
        await ctx.services.connection_manager.broadcast_to_players(recipients, message)


@dispatcher.action("end_game")
async def end_game(ctx: ActionContext, payload: ActionPayload) -> None:
    await ctx.services.game_service.end_game(_current_room_id(ctx), ctx.player.id)


class CardPayload(ActionPayload):
    card_id: int


@dispatcher.action("select_card", CardPayload)
async def select_card(ctx: ActionContext, payload: CardPayload) -> None:
    await ctx.services.game_service.player_select_card(_current_room_id(ctx), ctx.player.id, payload.card_id)


@dispatcher.action("choose_winner", CardPayload)
async def choose_winner(ctx: ActionContext, payload: CardPayload) -> None:
    await ctx.services.game_service.leader_choose_winner(_current_room_id(ctx), ctx.player.id, payload.card_id)


# --- chat ---


class ChatMessagePayload(ActionPayload):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


@dispatcher.action("chat_message", ChatMessagePayload)
async def chat_message(ctx: ActionContext, payload: ChatMessagePayload) -> None:
    recipients, message = await ctx.services.room_service.send_chat_message(
        room_id=_current_room_id(ctx),
        player=ctx.player,
        message=payload.text,
    )
    await ctx.services.connection_manager.broadcast_to_players(recipients, message)
