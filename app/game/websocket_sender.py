from fastapi import Depends

from app.game.dataclasses import Player
from app.game.game_manager import GameManager, get_game_manager


class WebSocketSender:
    def __init__(self, manager: "GameManager"):
        self.manager = manager

    def get_websocket_connection(self, player_id: str):
        websocket = self.manager.player_sockets.get(player_id)

        if not websocket:
            raise Exception("Socket not found!")

        return websocket

    async def send(self, player_id: str, event: str, payload: dict):
        websocket = self.get_websocket_connection(player_id)
        await websocket.send_json(
            {
                "event": event,
                "payload": payload,
            }
        )

    async def send_restore_state(self, player: Player):
        await self.send(
            player.id,
            event="restore_state",
            payload={
                "handed_cards": [card.dict() for card in player.handed_cards],
                "score": player.score,
                "is_host": player.is_host,
                # 'round_phase': ...,
            },
        )

    async def send_room_state(self, room_id: str, player: Player):
        game = self.manager.active_games.get(room_id)
        room = self.manager.active_rooms.get(room_id)

        await self.send(
            player.id,
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


def get_websocket_sender(manager: GameManager = Depends(get_game_manager)):
    return WebSocketSender(manager)
