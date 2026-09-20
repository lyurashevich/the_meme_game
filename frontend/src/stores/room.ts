import { defineStore } from "pinia"
import { ref } from "vue"

export const useRoomStore = defineStore("room", () => {
    const room = ref(null)

    return {
        room,
    }
})