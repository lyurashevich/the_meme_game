import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.dependencies import (
    get_connection_manager,
    get_game_manager,
    get_player_service,
    get_reconnect_service,
    get_room_service,
)
from app.exceptions import (
    GameNotFoundException,
    InvalidReconnectToken,
    PlayerNotFoundException,
)
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Player
from app.game.enums import WebsocketEvents
from app.game.game_manager import GameManager
from app.services.player_service import PlayerService
from app.services.reconnect_service import ReconnectService
from app.services.room_service import RoomService

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    reconnect_token: str | None = None,
    manager: GameManager = Depends(get_game_manager),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    player_service: PlayerService = Depends(get_player_service),
    reconnect_service: ReconnectService = Depends(get_reconnect_service),
    room_service: RoomService = Depends(get_room_service),
):
    await websocket.accept()

    player = None
    now = datetime.now(timezone.utc)

    if reconnect_token:
        try:
            player = await reconnect_service.handle_reconnect(reconnect_token, now)
            connection_manager.add_connection(player.id, websocket)

            token = await reconnect_service.create_reconnect_token(player.id)

            if not player.room_id:
                payload = (
                    player.id,
                    {
                        "event": WebsocketEvents.PLAYER_RECONNECTED.value,
                        "payload": {"reconnect_token": token, "avatar": player.avatar, "player_id": player.id},
                    },
                )
                await connection_manager.send_personal_json(*payload)
            else:
                payload = await build_reconnect_payload(manager, player, token, room_service)
                await connection_manager.send_personal_json(*payload)

        except (PlayerNotFoundException, InvalidReconnectToken):
            player = None

    if not player:
        player = player_service.create_player()
        connection_manager.add_connection(player.id, websocket)

        token = await reconnect_service.create_reconnect_token(player.id)

        await connection_manager.send_personal_json(
            player.id,
            {
                "event": WebsocketEvents.PLAYER_CREATED.value,
                "payload": {
                    "player_id": player.id,
                    "reconnect_token": token,
                    "username": player.username,
                    "avatar": player.avatar,
                },
            },
        )

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("event") == "chat_message":
                payload, recipients = await room_service.send_chat_message(  # type: ignore
                    room_id=message_data["room_id"],
                    player=player,
                    message=message_data["message"],
                )
                await connection_manager.broadcast_to_players(recipients, payload)  # type: ignore
            else:
                await websocket.send_text(f"echo: {data}")

    except WebSocketDisconnect:
        # normal disconnect
        pass
    except Exception:  # nosec B110
        # todo: add logging
        # ensure we don't leave player marked connected on unexpected errors
        # (logged elsewhere or in future)
        pass
    finally:
        if player:
            try:
                connection_manager.remove_connection(player.id)
                await reconnect_service.disconnect(player.id)
            except Exception:  # nosec B110
                # todo: add logging
                # swallow to avoid raising from websocket endpoint
                pass


@router.get("/{room_id}/messages")
async def get_room_messages(room_id: str, room_service: RoomService = Depends(get_room_service)):
    room = room_service.get_room(room_id)

    return room.messages[-50:]


async def build_reconnect_payload(
    manager: GameManager, player: Player, token: str, room_service: RoomService = Depends(get_room_service)
):
    if not player.room_id:
        return

    async with room_service.get_room_lock(room_id=player.room_id):
        room = room_service.get_room(player.room_id)
        payload_data: dict[str, Any] = {
            "reconnect_token": token,
            "room_id": player.room_id,
            "room_name": room.name,
            "avatar": player.avatar,
        }

        try:
            game = manager.get_game(player.room_id)
        except GameNotFoundException:
            game = None

        if game:
            payload_data.update(
                {
                    "players_choice": [
                        {"player_id": player_id, "card": card.to_dict()}
                        for player_id, card in game.current_round.player_choices.items()  # type: ignore[union-attr]
                    ],
                    "handed_cards": [card.to_dict() for card in player.handed_cards],
                    "score": player.score,
                    "is_host": player.is_host,
                    "players": (
                        [
                            {
                                "id": player.id,
                                "username": player.username,
                                "is_connected": player.is_connected,
                                "score": player.score,
                            }
                            for player in room.players
                        ]
                        if room
                        else []
                    ),
                    "game_state": game.state.value if game else None,
                    "round_state": (game.current_round.state.value if game and game.current_round else None),
                    "current_round_number": (game.current_round.round_number if game.current_round else None),
                    "leader_id": (game.current_round.leader_id if game.current_round else None),
                    "current_situation_card": (
                        game.current_round.situation_card.to_dict() if game.current_round else None
                    ),
                }
            )

        data = {"event": WebsocketEvents.PLAYER_RECONNECTED.value, "payload": payload_data}

        return player.id, data
