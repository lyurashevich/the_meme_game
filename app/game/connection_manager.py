import logging

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections independently from game logic.

    Responsibilities:
    - Store WebSocket connections (player_id -> websocket)
    - Get websocket by player_id
    - Send message to individual player
    - Broadcast message to all players in a room
    - Safe handling when websocket doesn't exist (no exceptions)
    """

    def __init__(self) -> None:
        # sockets are bound to this process, so they never go to shared storage
        self.player_sockets: dict[str, WebSocket] = {}  # player_id -> Websocket

    def add_connection(self, player_id: str, websocket: WebSocket) -> None:
        """Register a player connection."""
        self.player_sockets[player_id] = websocket

    def remove_connection(self, player_id: str, websocket: WebSocket) -> bool:
        """Forget ``websocket`` if it is still the player's current connection; return whether it was.

        A player who reconnected (say, after switching from Wi-Fi to mobile data) already has a new
        socket registered by the time the server notices the old one is dead. Closing the old one
        must not unregister the new one.
        """
        if self.player_sockets.get(player_id) is not websocket:
            return False

        del self.player_sockets[player_id]
        return True

    def get_connection(self, player_id: str) -> WebSocket | None:
        """Get websocket connection for a player (safe, returns None if not found)."""
        return self.player_sockets.get(player_id)

    # async def send_personal_message(self, player_id: str, message: str) -> None:
    #     """Send a message to a specific player (safe)."""
    #     websocket = self.get_connection(player_id)
    #     if websocket:
    #         try:
    #             await websocket.send_text(message)
    #         except Exception:  # nosec B110
    #             pass  # todo: add logging

    async def send_personal_json(self, player_id: str, data: dict) -> None:
        """Send a JSON message to a specific player (safe)."""
        websocket = self.get_connection(player_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception:
                logger.exception("Failed to send message to player %s", player_id)

    async def broadcast_to_players(self, player_ids: list[str], message: dict, exclude_id: str | None = None) -> None:
        """
        Broadcast JSON message to specific players (safe).

        Args:
            player_ids: List of player IDs to send to
            message: Dictionary to serialize as JSON
            exclude_id: If set, skip this player
        """
        for player_id in player_ids:
            if exclude_id and player_id == exclude_id:
                continue
            await self.send_personal_json(player_id, message)

    def clear(self) -> None:
        """Clear all connections (e.g. on server shutdown)."""
        self.player_sockets.clear()
