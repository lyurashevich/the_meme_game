from app.game.connection_manager import ConnectionManager
from app.game.game_manager import GameManager
from app.services.game_service import GameService
from app.services.player_service import PlayerService
from app.services.reconnect_service import ReconnectService
from app.services.room_service import RoomService

connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return connection_manager


game_manager = GameManager()


def get_game_manager() -> GameManager:
    return game_manager


room_service = RoomService()


def get_room_service() -> RoomService:
    return room_service


player_service = PlayerService(connection_manager=connection_manager, room_service=room_service)


def get_player_service() -> PlayerService:
    return player_service


game_service = GameService(room_service, game_manager, connection_manager)


def get_game_service() -> GameService:
    return game_service


reconnect_service = ReconnectService(room_service, player_service)


def get_reconnect_service() -> ReconnectService:
    return reconnect_service
