import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { useGameStore } from './store/gameStore';

// Connect once, when the page loads - not from a component, which React may mount and unmount
// several times (StrictMode does it on purpose in development to catch missing cleanups).
useGameStore.getState().connect();

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
