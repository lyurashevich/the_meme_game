import { apiFetch } from "../api.ts";
import type { GameRoom } from "../types.ts";

export const joinRoom = (room: GameRoom, playerId: string) => {
    return apiFetch<GameRoom>(`/room/${room.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
            player_id: playerId,
            room_id: room.id,
            confirm: false,
        }),
    });
};

export const createRoom = (room: GameRoom, playerId: string) => {
    return apiFetch<GameRoom>('/room/', {
        method: 'POST',
        body: JSON.stringify({player_id: playerId,
            name: room.name,
        max_players: room.maxPlayers,
        is_private: room.isPrivate,})
    });
};

export const loadRooms = () => {
    return apiFetch<GameRoom[]>('/room/all')
}