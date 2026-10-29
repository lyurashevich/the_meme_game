"""Storage interfaces for in-game state (rooms, players, games, reconnect tokens).

Services talk to these interfaces only, so the in-memory implementation can be
swapped for a shared one (e.g. Redis) without touching game logic. Methods are
async even though the in-memory implementation doesn't need it: a networked
store does.
"""

from abc import ABC, abstractmethod

from app.game.dataclasses import Game, Player, ReconnectToken, Room


class RoomRepository(ABC):
    @abstractmethod
    async def get(self, room_id: str) -> Room | None: ...

    @abstractmethod
    async def list(self) -> list[Room]: ...

    @abstractmethod
    async def add(self, room: Room) -> None: ...

    @abstractmethod
    async def remove(self, room_id: str) -> None: ...


class PlayerRepository(ABC):
    @abstractmethod
    async def get(self, player_id: str) -> Player | None: ...

    @abstractmethod
    async def list(self) -> list[Player]: ...

    @abstractmethod
    async def add(self, player: Player) -> None: ...

    @abstractmethod
    async def remove(self, player_id: str) -> None: ...


class GameRepository(ABC):
    """Games are keyed by the id of the room they are played in."""

    @abstractmethod
    async def get(self, room_id: str) -> Game | None: ...

    @abstractmethod
    async def add(self, room_id: str, game: Game) -> None: ...

    @abstractmethod
    async def remove(self, room_id: str) -> None: ...


class ReconnectTokenRepository(ABC):
    """Stores reconnect tokens; a player has at most one token at a time."""

    @abstractmethod
    async def get(self, token: str) -> ReconnectToken | None: ...

    @abstractmethod
    async def get_token_for_player(self, player_id: str) -> str | None: ...

    @abstractmethod
    async def add(self, token: str, entry: ReconnectToken) -> None: ...

    @abstractmethod
    async def remove(self, token: str) -> ReconnectToken | None:
        """Remove the token and return its entry, or ``None`` if it didn't exist."""

    @abstractmethod
    async def list(self) -> list[tuple[str, ReconnectToken]]: ...
