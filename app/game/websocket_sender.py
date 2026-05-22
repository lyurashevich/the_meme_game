from starlette.websockets import WebSocket

from app.game.dataclasses import Player
from app.game.game_manager import GameManager


class WebSocketSender:
    def __init__(self, manager: "GameManager"):
        self.manager = manager

    @staticmethod
    async def send(websocket: WebSocket, event: str, payload: dict):
        await websocket.send_json(
            {
                "event": event,
                "payload": payload,
            }
        )

    async def send_restore_state(self, websocket: WebSocket, player: Player):
        await self.send(
            websocket,
            event="restore_state",
            payload={
                "handed_cards": [card.dict() for card in player.handed_cards],
                "score": player.score,
                "is_host": player.is_host,
                # 'round_phase': ...,
            },
        )

    async def send_room_state(self, websocket: WebSocket, room_id: str):
        game = self.manager.active_games.get(room_id)
        room = self.manager.active_rooms.get(room_id)

        await self.send(
            websocket,
            "room_state",
            {
                "room_id": room_id,
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
                "game_state": game.state if game else None,
                "round_state": game.current_round.state if game and game.current_round else None,
                # 'time_left': ...,
            },
        )
