from asyncio import Task
from dataclasses import dataclass, field

from app.exceptions import (
    AlreadyInARoomException,
    GameNotFoundException,
)
from app.game.dataclasses import Game


@dataclass
class GameManager:
    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    player_connections: dict[str, str] = field(default_factory=dict)  # player_id -> room_id
    room_tasks: dict[str, dict[str, Task]] = field(default_factory=dict)  # room_id -> {task_name -> Task}

    @property
    def players_in_rooms(self) -> set[str]:
        return set(self.player_connections)

    def remove_player_connection(self, player_id: str) -> None:
        self.player_connections.pop(player_id, None)

    def add_player_connection(self, player_id: str, room_id: str) -> None:
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

    def add_task(self, room_id: str, name: str, task: Task) -> None:
        room_tasks = self.room_tasks.setdefault(room_id, {})

        old_task = room_tasks.get(name)
        if old_task and not old_task.done():
            old_task.cancel()

        room_tasks[name] = task

    def cancel_task(self, room_id: str, name: str) -> None:
        task = self.room_tasks.get(room_id, {}).pop(name, None)
        if task:
            task.cancel()

    def clear_room_tasks(self, room_id: str) -> None:
        room_tasks = self.room_tasks.pop(room_id, {})
        for task in room_tasks.values():
            task.cancel()
