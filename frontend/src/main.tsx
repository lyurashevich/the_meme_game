import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { soundFor } from './sounds/gameSounds';
import { playSound, unlockAudioOnFirstGesture } from './sounds/synth';
import { useGameStore } from './store/gameStore';
import { useSoundStore } from './store/soundStore';

// Connect once, when the page loads - not from a component, which React may mount and unmount
// several times (StrictMode does it on purpose in development to catch missing cleanups).
useGameStore.getState().connect();

// Sounds for what happens in the game: every change of the game data is checked for one
unlockAudioOnFirstGesture(window);
useGameStore.subscribe((next, prev) => {
  if (useSoundStore.getState().muted) return;
  const sound = soundFor(prev, next);
  if (sound) playSound(sound);
});

if (import.meta.env.DEV) {
  // For poking at the store from the browser console: game.getState(), game.getState().createRoom({})
  Object.assign(window, { game: useGameStore });
}

// index.html has an empty <div id="root">; React renders the whole app inside it.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
