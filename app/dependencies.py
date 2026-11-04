import secrets
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings
from app.exceptions import AdminApiDisabledException, InvalidAdminTokenException
from app.game.connection_manager import ConnectionManager
from app.game.game_manager import GameManager
from app.repositories.in_memory import (
    InMemoryGameRepository,
    InMemoryPlayerRepository,
    InMemoryReconnectTokenRepository,
    InMemoryRoomRepository,
)
from app.services.game_service import GameService
from app.services.notifier import Notifier
from app.services.player_service import PlayerService
from app.services.reconnect_service import ReconnectService
from app.services.room_service import RoomService


@dataclass
class Services:
    connection_manager: ConnectionManager
    game_manager: GameManager
    room_service: RoomService
    player_service: PlayerService
    notifier: Notifier
    game_service: GameService
    reconnect_service: ReconnectService


def build_services() -> Services:
    """Wire up the services with fresh storage. Swap the repositories here to change the backend."""
    connection_manager = ConnectionManager()
    game_manager = GameManager(InMemoryGameRepository())
    room_service = RoomService(InMemoryRoomRepository())
    player_service = PlayerService(InMemoryPlayerRepository(), room_service)
    notifier = Notifier(connection_manager, room_service, game_manager, player_service)
    game_service = GameService(room_service, game_manager, notifier)
    reconnect_service = ReconnectService(InMemoryReconnectTokenRepository(), player_service, game_service)

    return Services(
        connection_manager=connection_manager,
        game_manager=game_manager,
        room_service=room_service,
        player_service=player_service,
        notifier=notifier,
        game_service=game_service,
        reconnect_service=reconnect_service,
    )


services = build_services()


def get_services() -> Services:
    return services


def get_connection_manager() -> ConnectionManager:
    return services.connection_manager


def get_game_manager() -> GameManager:
    return services.game_manager


def get_room_service() -> RoomService:
    return services.room_service


def get_player_service() -> PlayerService:
    return services.player_service


def get_game_service() -> GameService:
    return services.game_service


def get_reconnect_service() -> ReconnectService:
    return services.reconnect_service


# Declared as a security scheme so Swagger UI (/docs) offers an "Authorize" field for it
admin_token_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def require_admin(
    token: str | None = Depends(admin_token_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Guards endpoints that change the card database. Closed unless ADMIN_TOKEN is configured."""
    if not settings.admin_token:
        raise AdminApiDisabledException()

    # constant-time comparison: how long a wrong token takes to reject reveals nothing about it
    if token is None or not secrets.compare_digest(token.encode(), settings.admin_token.encode()):
        raise InvalidAdminTokenException()
