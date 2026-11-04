import { createReadStream, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import type { Plugin } from 'vite';
import { defineConfig } from 'vitest/config'; // Vite's own config plus the `test` section

// Where the backend runs: uvicorn on port 8000 locally, the "backend" service in docker-compose.
const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000';

// The meme pictures: media/ in the project root (docker-compose mounts it at /media and says so in
// MEDIA_DIR). In production nginx serves the same /media/ addresses; see nginx/default.conf.template.
const mediaDir = path.resolve(process.env.MEDIA_DIR ?? fileURLToPath(new URL('../media', import.meta.url)));

// Only pictures: nothing else that might end up in the folder is given out
const PICTURE_TYPES: Record<string, string> = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
};

/** The dev server gives out the files of mediaDir at /media/... , as nginx does in production. */
function serveMedia(): Plugin {
  return {
    name: 'serve-media',
    configureServer(server) {
      // Added before Vite's own handlers; req.url is what follows /media, e.g. /memes/3f9a1c.jpg
      server.middlewares.use('/media', (req, res) => {
        let file: string;
        try {
          file = path.join(mediaDir, decodeURIComponent((req.url ?? '/').split('?')[0]));
        } catch {
          res.statusCode = 400; // broken %-encoding
          return res.end();
        }
        const type = PICTURE_TYPES[path.extname(file).toLowerCase()];
        // path.join has already resolved any "..": whatever is left must still be inside mediaDir
        const isInside = file.startsWith(mediaDir + path.sep);
        const size = isInside && type ? fileSize(file) : undefined;
        if (size === undefined) {
          res.statusCode = 404;
          return res.end();
        }
        res.setHeader('Content-Type', type);
        res.setHeader('Content-Length', size);
        createReadStream(file).pipe(res);
      });
    },
  };
}

function fileSize(file: string): number | undefined {
  try {
    const stats = statSync(file);
    return stats.isFile() ? stats.size : undefined;
  } catch {
    return undefined; // no such file
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), serveMedia()],
  server: {
    // The page and the backend live on different ports; the dev server forwards these paths to the
    // backend, so the browser only ever talks to one address (and needs no CORS setup).
    proxy: {
      '/api': backendUrl,
      '/ws': { target: backendUrl, ws: true },
    },
  },
  test: {
    environment: 'node', // the tests don't touch the page, so no browser emulation is needed
  },
});
