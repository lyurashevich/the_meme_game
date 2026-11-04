# 🎭 The Meme Game 🎭

*Because who doesn't want to judge memes while pretending to be funny?*

## What's This All About? 🤔

Welcome to the most chaotic, hilarious, and slightly unhinged meme card game you'll ever play! Think Cards Against Humanity, but with memes and your friends' questionable sense of humor.

Players take turns being the "judge" (we call them leaders because it sounds more important), while everyone else tries to match the perfect meme to a ridiculous situation. The best part? You get to roast your friends' choices in the chat in real time! 🔥

## How to Play (The Rules That Matter) 🎮

1. **Gather your squad** 👥 — 3 to 10 players in a room. The room owner sets the time per turn (60, 90 or 120 s) and, if they like, a limit of rounds or points.
2. **Get your cards** 🃏 — everyone gets 6 meme cards. The room owner is the first leader.
3. **The round begins** ⚡ — a situation card goes on the table, and everyone except the leader plays one meme from their hand before the time runs out.
4. **The judgement** 👨‍⚖️ — the leader sees the memes without their authors and has 30 seconds to pick the best one. Its author gets +1 point.
5. **Keep the party going** 🔄 — everyone who played a meme draws a new card, and the next player becomes the leader.
6. **The end** 🏁 — the game ends when the owner says so, a round or point limit is reached, fewer than 3 players are left, or the deck runs out. Everyone sees the final scores.

The small print:
- Played memes rest for 10 rounds and situations for 20 before they can come up again.
- Names are unique within a room, ignoring case ("Neo" and "neo" are the same name).
- Lost your connection? You have 60 seconds to come back and keep your place. A leader who is away doesn't hold the game up for longer than their 30 seconds.
- When everyone has left, the room disappears.

## Tech Stuff (For the Nerds) 💻

| | |
|---|---|
| Frontend | React 19 + TypeScript, Vite, Tailwind, Zustand (`frontend/`) |
| Backend | FastAPI: every game action goes over one WebSocket (`/ws`); REST only for reading cards and editing them (`/api`) |
| Database | PostgreSQL — the cards and nothing else |
| Game state | In the backend's memory: rooms, players, games. One backend process (Redis is planned) |
| Production | nginx serves the built frontend and passes `/api` and `/ws` on to the backend; all in Docker |

After every change, each player gets a full personal snapshot of their room (`room_state`), so the client never has to stitch updates together and reconnecting works the same way. The protocol is described in [docs/mvp-plan.md](docs/mvp-plan.md) ("WS-протокол").

```
app/          backend: views (REST, /ws), websockets (actions), services (game logic), game (state)
migrations/   database migrations (alembic)
scripts/      loading test memes and situations
tests/        backend tests (pytest)
frontend/     the game: src/screens, src/components, src/store (Zustand), src/api (WebSocket client)
docs/         the plan and the protocol
```

## Getting Started (The Not-So-Boring Part) 🚀

Two ways: run everything yourself (the quickest loop while coding) or everything in Docker.

### Option A: on your machine

You need Python 3.12, Node 22 (see `frontend/.nvmrc`) and PostgreSQL 15 or newer.

1. **Install the dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt

   cd frontend && npm install && cd ..
   ```

2. **Settings**
   ```bash
   cp .env.example .env
   ```
   Fill in the database part; every variable is explained in the file.

3. **Two databases**: one for the game, one for the tests (the tests empty its tables). The user from `.env` must own both:
   ```bash
   sudo -u postgres psql -c "CREATE USER meme WITH PASSWORD 'change-me';"
   sudo -u postgres createdb -O meme meme_game
   sudo -u postgres createdb -O meme meme_game_test
   ```

4. **Tables**
   ```bash
   alembic upgrade head
   ```

5. **Cards** (see [Cards](#cards-) below)
   ```bash
   python -m scripts.load_memes ~/path/to/folder/with/pictures
   python -m scripts.load_situations
   ```

6. **Start the party**
   ```bash
   uvicorn app.main:app --reload --port 8000      # terminal 1, project root
   cd frontend && npm run dev                     # terminal 2
   ```
   Open http://localhost:5173. Every browser tab is a separate player, so three tabs are enough to play alone.

Run everything from the project root (`frontend` only for `npm`); `.env` is always found there.

### Option B: Docker for development

```bash
cp .env.example .env               # and fill it in
docker compose up --build
```

`docker-compose.yml` (database and backend) is combined with `docker-compose.override.yml`, which compose picks up on its own. The code is mounted from your machine, so both servers reload on changes.

| Address | What |
|---|---|
| http://localhost:5173 | the game |
| http://localhost:8000/docs | the backend's Swagger |
| `localhost:5433` | the database |

To load cards into this database, point the scripts at its port:
```bash
DB_PORT=5433 python -m scripts.load_memes ~/path/to/folder/with/pictures
DB_PORT=5433 python -m scripts.load_situations
```

A port already taken? Change `DB_DOCKER_PORT`, `BACKEND_PORT` or `FRONTEND_PORT` in `.env`.

### Option C: production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Only nginx is open to the outside (port `WEB_PORT`, 80 by default); the database and the backend are reachable by the other containers only, and everything restarts after a crash or a reboot.

The meme pictures live in the `media` Docker volume, which nginx gives out at `/media/`; it outlives the containers, so rebuilding the app keeps them. Loading cards into it is still to come (see [Cards](#cards-)).

## Cards 🃏

**Where the pictures are.** The database keeps only each picture's key, e.g. `memes/3f9a1c.jpg`; the browser loads it from `MEDIA_BASE_URL` plus the key (`/media/memes/3f9a1c.jpg`, the same site as the game). The files themselves:

| Running | Folder | Given out at `/media/` by |
|---|---|---|
| on your machine (option A) | `media/` in the project root (`MEDIA_DIR`) | the Vite dev server |
| Docker for development (option B) | the same `media/`, mounted into the containers | the Vite dev server |
| production (option C) | the `media` Docker volume | nginx, cached by the browser for a month |

Only pictures (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`) are given out, nothing else from the folder.

**Memes** are pictures. For local testing:
```bash
python -m scripts.load_memes ~/path/to/folder/with/pictures
```
copies the pictures to `frontend/public/memes/` (not in git) and adds a card for each, with an address on the Vite dev server (`http://localhost:5173/memes/...`). The pictures load while `npm run dev` (or the `frontend` container) is running.

**Situations** are texts, one per line in a file; empty lines and lines starting with `#` are skipped:
```bash
python -m scripts.load_situations                  # 25 test ones from scripts/situations.txt
python -m scripts.load_situations my_situations.txt
```

Both scripts print which database they use and can be run again: what is already there is skipped.

How many you need: a full room of 10 needs 150 memes to never run out (6 per player in hand plus those resting after being played), 4 players need 54; 21 situations are enough for any game.

**Editing cards over HTTP**: `POST/PATCH/DELETE /api/memes/` and `/api/situations/` need the header `X-Admin-Token` equal to `ADMIN_TOKEN` from `.env`; with no token set, editing is off. Reading (`GET`) is open. Swagger (`/docs`) has an "Authorize" button for the token.

## Tests and Checks 🧪

**Backend** (needs the test database, `TEST_DB_NAME`):
```bash
pytest
black --check --line-length=120 . && flake8 && isort --check-only --profile black .
```

**Frontend** (in `frontend/`):
```bash
npm test               # Vitest
npm run lint           # ESLint
npm run format:check   # Prettier (npm run format fixes it)
npm run build          # type check and production build
```

GitHub Actions runs all of it on every push to `dev` and every pull request to `main`; the backend tests get a PostgreSQL of their own there.

## Troubleshooting (When Things Go Wrong) 🔧

| You see | Why, and what to do |
|---|---|
| `DatabaseNotConfiguredError: PostgreSQL is not configured: set ...` | `.env` is missing or lacks the variables named in the message. |
| `database "..." does not exist` | Create it: `sudo -u postgres createdb -O <user> <name>`. |
| `permission denied for schema public` | The database belongs to another user, and since PostgreSQL 15 only the owner may create tables: `ALTER DATABASE <name> OWNER TO <user>;` |
| `template database "template1" has a collation version mismatch` | The system's libraries were updated. For the empty template it's safe: `sudo -u postgres psql -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;"` |
| The backend in Docker can't log in to the database | The `pgdata` volume was created with other credentials: PostgreSQL takes them only when the volume is new. `docker compose down -v` recreates it (and deletes the data in it). |
| `pytest.UsageError: TEST_DB_NAME is the same as DB_NAME` | On purpose: the tests empty the tables of their database. Give them a separate one. |
| The game shows "Нет связи, переподключаемся" | The backend isn't running, or not on port 8000. |
| Every player suddenly became a new one | The backend restarted (with `--reload`, on any saved `.py` file): the game state lives in its memory. |
| "Картинка не загрузилась" on the cards | Locally: the Vite dev server isn't running, it serves the pictures. Or the file isn't in the media folder (see [Cards](#cards-)). |
| `Orphan containers` warning from compose | Containers left from older service names: `docker compose up --remove-orphans`. |

## Contributing (We Want Your Memes!) 🤝

1. Create a branch from `dev`: `git checkout -b feature/amazing-meme-addition`
2. Make sure the checks above pass
3. Open a pull request (CI checks every push to `dev` and every pull request into `main`)

## Acknowledgments (Shoutouts!) 🙏

- Thanks to all the meme creators who made this possible
- Special thanks to Cards Against Humanity for the inspiration
- Shoutout to FastAPI for making our lives easier
- Big thanks to WebSockets for the real-time magic

## Contact (Find Us!) 📞

- GitHub: [@vinogradovalisaveta](https://github.com/vinogradovalisaveta)
- Email: lizaveta.yurashevich@gmail.com

---

*Remember: The best memes are the ones that make your friends question your sanity. Happy gaming! 🎉*
