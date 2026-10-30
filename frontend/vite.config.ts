import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Where the backend runs: uvicorn on port 8000 locally, the "fastapi" service in docker-compose.
const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // The page and the backend live on different ports; the dev server forwards these paths to the
    // backend, so the browser only ever talks to one address (and needs no CORS setup).
    proxy: {
      '/api': backendUrl,
      '/ws': { target: backendUrl, ws: true },
    },
  },
});
