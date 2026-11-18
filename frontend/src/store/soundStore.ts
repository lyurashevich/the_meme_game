// Whether the sounds are on. A choice for this device, so it is kept in localStorage.
import { create } from 'zustand';

const MUTED_KEY = 'sound_muted';

interface SoundStore {
  muted: boolean;
  toggleMuted: () => void;
}

export const useSoundStore = create<SoundStore>()((set, get) => ({
  muted: localStorage.getItem(MUTED_KEY) === 'true',

  toggleMuted: () => {
    const muted = !get().muted;
    localStorage.setItem(MUTED_KEY, String(muted));
    set({ muted });
  },
}));
