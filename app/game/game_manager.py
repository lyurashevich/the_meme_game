from dataclasses import dataclass, field

from app.game.dataclasses import Game, Player, Room


@dataclass
class GameManager:

    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    active_rooms: dict[str, Room] = field(default_factory=dict)  # room_id -> Room
    player_connections: dict[int, str] = field(default_factory=dict)  # player_id -> room_id

    async def create_room(
        self,
        owner: Player,
        room_name: str | None = None,
        max_players: int = 10,
        is_private: bool = False,
    ) -> Room:
        room = Room(owner=owner, name=room_name, max_players=max_players, is_private=is_private)

        self.active_rooms[room.id] = room
        self.player_connections[owner.id] = room.id

        return room

    async def join_room(self, room_id: str, player: Player) -> None:

        if room_id not in self.active_rooms:
            raise Exception("Room not found")

        room = self.active_rooms[room_id]
        await room.add_player(player)
        self.player_connections[player.id] = room_id

    async def leave_room(self, player_id: int) -> None:
        if player_id not in self.player_connections:
            raise Exception("Player not found")

        room_id = self.player_connections[player_id]
        if room_id not in self.active_rooms:
            raise Exception("Room not found")

        room = self.active_rooms[room_id]
        player = next((player for player in room.players if player.id == player_id), None)

        if not player:
            raise Exception("Player not found")

        await room.remove_player(player)
        del self.player_connections[player_id]

        if not room.players:
            await self.cleanup_room(room_id)

    async def cleanup_room(self, room_id):
        if room_id in self.active_games:
            del self.active_games[room_id]

        if room_id in self.active_rooms:
            del self.active_rooms[room_id]

        players_to_remove = [player_id for player_id, room in self.player_connections.items() if room == room_id]
        for player_id in players_to_remove:
            del self.player_connections[player_id]


game_manager = GameManager()
