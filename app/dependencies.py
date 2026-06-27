from app.game.connection_manager import ConnectionManager
from app.game.game_manager import GameManager
from app.game.websocket_sender import WebSocketSender
from app.services.player_service import PlayerService

connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return connection_manager


game_manager = GameManager()


def get_game_manager() -> GameManager:
    return game_manager


websocket_sender = WebSocketSender(connection_manager=connection_manager)


def get_websocket_sender() -> WebSocketSender:
    return websocket_sender


game_manager.websocket_sender = websocket_sender


player_service = PlayerService(manager=game_manager, sender=websocket_sender, connection_manager=connection_manager)


def get_player_service() -> PlayerService:
    return player_service
