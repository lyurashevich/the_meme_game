// Short messages in the corner of the screen ("toasts") that go away on their own.
// A store of their own, so anything can show one - a screen, App, the socket code -
// without passing a function down through the components.
import { create } from 'zustand';

const SHOW_FOR_MS = 5000;

export interface Toast {
  id: number;
  text: string;
}

interface ToastStore {
  toasts: Toast[];
  show: (text: string) => void;
  dismiss: (id: number) => void;
}

let lastId = 0;
const timers = new Map<number, ReturnType<typeof setTimeout>>();

export const useToastStore = create<ToastStore>()((set, get) => ({
  toasts: [],

  show: (text) => {
    // The same text again (a button pressed twice) doesn't pile up: the old toast just stays longer
    const same = get().toasts.find((toast) => toast.text === text);
    const id = same?.id ?? ++lastId;
    if (!same) set((state) => ({ toasts: [...state.toasts, { id, text }] }));

    clearTimeout(timers.get(id));
    timers.set(
      id,
      setTimeout(() => get().dismiss(id), SHOW_FOR_MS),
    );
  },

  dismiss: (id) => {
    clearTimeout(timers.get(id));
    timers.delete(id);
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  },
}));

// For code outside components: showToast('...')
export const showToast = (text: string) => useToastStore.getState().show(text);
