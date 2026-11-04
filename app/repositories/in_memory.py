from app.game.dataclasses import Game, Player, ReconnectToken, Room
from app.repositories.base import (
    GameRepository,
    PlayerRepository,
    ReconnectTokenRepository,
    RoomRepository,
)


class InMemoryRoomRepository(RoomRepository):
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}  # room_id -> Room

    async def get(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    async def list(self) -> list[Room]:
        return list(self._rooms.values())

    async def add(self, room: Room) -> None:
        self._rooms[room.id] = room

    async def remove(self, room_id: str) -> None:
        self._rooms.pop(room_id, None)


class InMemoryPlayerRepository(PlayerRepository):
    def __init__(self) -> None:
        self._players: dict[str, Player] = {}  # player_id -> Player

    async def get(self, player_id: str) -> Player | None:
        return self._players.get(player_id)

    async def list(self) -> list[Player]:
        return list(self._players.values())

    async def add(self, player: Player) -> None:
        self._players[player.id] = player

    async def remove(self, player_id: str) -> None:
        self._players.pop(player_id, None)


class InMemoryGameRepository(GameRepository):
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}  # room_id -> Game

    async def get(self, room_id: str) -> Game | None:
        return self._games.get(room_id)

    async def add(self, room_id: str, game: Game) -> None:
        self._games[room_id] = game

    async def remove(self, room_id: str) -> None:
        self._games.pop(room_id, None)


class InMemoryReconnectTokenRepository(ReconnectTokenRepository):
    def __init__(self) -> None:
        self._tokens: dict[str, ReconnectToken] = {}  # token -> ReconnectToken
        self._player_tokens: dict[str, str] = {}  # player_id -> token

    async def get(self, token: str) -> ReconnectToken | None:
        return self._tokens.get(token)

    async def get_token_for_player(self, player_id: str) -> str | None:
        return self._player_tokens.get(player_id)

    async def add(self, token: str, entry: ReconnectToken) -> None:
        self._tokens[token] = entry
        self._player_tokens[entry.player_id] = token

    async def remove(self, token: str) -> ReconnectToken | None:
        entry = self._tokens.pop(token, None)
        if entry and self._player_tokens.get(entry.player_id) == token:
            del self._player_tokens[entry.player_id]
        return entry

    async def list(self) -> list[tuple[str, ReconnectToken]]:
        return list(self._tokens.items())
