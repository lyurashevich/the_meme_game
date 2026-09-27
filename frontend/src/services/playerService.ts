import { apiFetch } from "../api.ts";
import type { PlayerProfile } from "../types.ts";

export const createPlayer = (player: PlayerProfile) => {
    return apiFetch<PlayerProfile>('/player/', {
        method: 'POST',
        body: JSON.stringify({username: player.username,
        avatar_id: player.avatarId}),
    });
};