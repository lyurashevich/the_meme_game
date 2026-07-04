from asyncio import Task
from dataclasses import dataclass, field

from app.exceptions import (
    AlreadyInARoomException,
    GameNotFoundException,
)
from app.game.dataclasses import Game

RECONNECT_TIMEOUT = 60  # seconds


@dataclass
class GameManager:
    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    room_tasks: dict[str, dict[str, Task]] = field(default_factory=dict)  # room_id -> {task_name -> Task}

    def delete_player_from_player_connections(self, player_id: str):
        del self.player_connections[player_id]

    def add_player_to_player_connections(self, player_id: str, room_id: str) -> None:
        self.player_connections[player_id] = room_id

    def validate_player_can_join_room(self, player_id: str) -> bool:
        if player_id in self.player_connections:
            raise AlreadyInARoomException()

        return True

    def get_game(self, room_id: str) -> Game:
        game = self.active_games.get(room_id)

        if not game:
            raise GameNotFoundException()

        return game
