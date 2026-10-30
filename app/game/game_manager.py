from asyncio import Task, current_task

from app.exceptions import (
    AlreadyInARoomException,
    GameNotFoundException,
)
from app.game.dataclasses import Game, Player
from app.repositories.base import GameRepository


class GameManager:
    def __init__(self, games: GameRepository):
        self.games = games
        # asyncio tasks are bound to this process's event loop, so they stay local
        self.room_tasks: dict[str, dict[str, Task]] = {}  # room_id -> {task_name -> Task}

    @staticmethod
    def validate_player_can_join_room(player: Player) -> bool:
        if player.room_id:
            raise AlreadyInARoomException()

        return True

    async def get_game(self, room_id: str) -> Game:
        game = await self.games.get(room_id)

        if not game:
            raise GameNotFoundException()

        return game

    async def add_game(self, room_id: str, game: Game) -> None:
        await self.games.add(room_id, game)

    def add_task(self, room_id: str, name: str, task: Task) -> None:
        room_tasks = self.room_tasks.setdefault(room_id, {})

        old_task = room_tasks.get(name)
        if old_task and not old_task.done():
            self._cancel(old_task)

        room_tasks[name] = task

    def cancel_task(self, room_id: str, name: str) -> None:
        task = self.room_tasks.get(room_id, {}).pop(name, None)
        if task:
            self._cancel(task)

    def clear_room_tasks(self, room_id: str) -> None:
        room_tasks = self.room_tasks.pop(room_id, {})
        for task in room_tasks.values():
            self._cancel(task)

    @staticmethod
    def _cancel(task: Task) -> None:
        # A room task (e.g. the phase timer) may itself finish the round or the game and thus
        # ask to cancel its own entry. Cancelling it would abort it at its next await -
        # right before it broadcasts the result - so it is only dropped from the registry.
        if task is not current_task():
            task.cancel()
