from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Game, Player, Room


class WebSocketSender:
    def __init__(self, connection_manager: "ConnectionManager"):
        self.connection_manager = connection_manager

    async def send(self, player_id: str, event: str, payload: dict):
        await self.connection_manager.send_personal_json(
            player_id,
            {
                "event": event,
                "payload": payload,
            },
        )

    async def send_restore_state(self, player: Player):
        await self.send(
            player.id,
            event="restore_state",
            payload={
                "handed_cards": [card.to_dict() for card in player.handed_cards],
                "score": player.score,
                "is_host": player.is_host,
                # 'round_phase': ...,
            },
        )

    async def send_room_state(self, room: Room, player: Player, game: Game | None = None):

        await self.send(
            player.id,
            "room_state",
            {
                "room_id": room.id,
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
                "round_state": (game.current_round.state if game and game.current_round else None),
                # 'time_left': ...,
            },
        )

    async def send_round_state_changed(self, room: Room, round_state: str):

        for player in room.players:
            await self.send(player.id, "round_state_changed", {"state": round_state})

    async def send_first_round_started(self, game: Game):

        for player in game.room.players:

            payload = {
                "room_id": game.room.id,
                "leader_id": (game.current_round.leader_id if game and game.current_round else None),
                "current_round_number": (game.current_round.round_number if game and game.current_round else None),
                "current_situation_card": (
                    game.current_round.situation_card.to_dict() if game and game.current_round else None
                ),
                "score": {player.id: player.score for player in game.room.players},
                "players": [player.username for player in game.room.players],
                "player_cards": [card.to_dict() for card in player.handed_cards],
            }

            await self.send(player.id, "first_round_started", payload)
