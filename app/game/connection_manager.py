from starlette.websockets import WebSocket


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

    player_sockets: dict[str, WebSocket | None] = {}  # player_id -> Websocket

    def add_connection(self, player_id: str, websocket: WebSocket) -> None:
        """Register a player connection."""
        self.player_sockets[player_id] = websocket

    def remove_connection(self, player_id: str) -> None:
        """Remove player connection."""
        self.player_sockets.pop(player_id, None)

    def get_connection(self, player_id: str) -> WebSocket | None:
        """Get websocket connection for a player (safe, returns None if not found)."""
        return self.player_sockets.get(player_id)

    async def send_personal_message(self, player_id: str, message: str) -> None:
        """Send a message to a specific player (safe)."""
        websocket = self.get_connection(player_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception:  # nosec B110
                pass  # todo: add logging

    async def send_personal_json(self, player_id: str, data: dict) -> None:
        """Send a JSON message to a specific player (safe)."""
        websocket = self.get_connection(player_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception:  # nosec B110
                pass  # todo: add logging
                # print("CONNECTION_MANAGER.PY LINE 46:", traceback.print_exc())

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
