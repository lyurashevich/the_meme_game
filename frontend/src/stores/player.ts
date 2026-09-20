import { defineStore } from "pinia";
import { ref } from "vue";
import type { PlayerProfile } from "../types.ts";

export const usePlayerStore = defineStore("player", () => {
    const player = ref<PlayerProfile | null>(null)

    return {
        player,
    }
})