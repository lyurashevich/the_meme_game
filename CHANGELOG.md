# Changelog

What changed from version to version. Versions follow [semantic versioning](https://semver.org/): the first number grows with changes that break something for players or for whoever runs the game, the second with new features, the third with fixes.

## [1.1.0] - 2026-11-20

Easier to see what to do, nicer to watch, and a reason to stay for one more game.

### Game
- "Play again": the owner starts a new game right from the final scores, with the same players.
- The game settings can be chosen when creating a room; the settings window is bigger.
- A meme and the round's winner are confirmed with a button on the picked card itself, and the hints name that button.
- The situation sits below the played memes, the face-down cards have a designed back instead of a caption.
- The winning meme pops out and the others step back; confetti for the winner of a round, a confetti rain and a wiggling trophy for the winner of the game.
- Sounds for a new round, the leader's turn to judge, a won round, the end of the game and chat messages, with a button in the header to turn them off.
- A closed tab or browser opened again within 60 seconds comes back as the same player.
- More situations, some of them 18+.
- The page has a title and a description for search results and link previews.

### Running the game
- Production is served over HTTPS: Caddy in front of nginx gets and renews a Let's Encrypt certificate for `SITE_ADDRESS` from `.env`. It replaces `WEB_PORT`; ports 80 and 443 are used.
- The new situations are added with `python -m scripts.load_cards situations`; the ones already in the database are skipped.

## [1.0.0] - 2026-11-05

The first playable version: from creating a profile to the final scores, for 3 to 10 players.

### Game
- Profiles with a nickname and an avatar; names are unique within a room, ignoring case.
- Rooms: a list with their host, players and settings; create, join, chat in the lobby.
- Settings for the room owner: time per turn (60, 90 or 120 s), an optional limit of rounds or points.
- Rounds: a situation on the table, everyone but the leader plays one of their 6 memes in time, the leader picks the best one in 30 s without seeing the authors (+1 point), hands are filled back up to 6, the next player leads.
- The game ends when the owner ends it, a limit is reached, fewer than 3 players are left or the decks run out; everyone sees the final scores.
- 60 seconds to reconnect and keep your place and score.
- Chat with quick reactions, the rules of the game in a window.

### Under the hood
- React 19 + TypeScript frontend; every game action over one WebSocket, with a full personal snapshot of the room after every change.
- Server-driven phase timers; consistent dealing, card cooldowns (10 rounds for memes, 20 for situations), an atomic game start.
- PostgreSQL with Alembic migrations; meme pictures stored as files, served at `/media/`, loaded by `scripts/load_cards.py`.
- Docker setup for development and production (nginx in front); CI for the backend and the frontend.

[1.1.0]: https://github.com/lyurashevich/the_meme_game/releases/tag/v1.1.0
[1.0.0]: https://github.com/lyurashevich/the_meme_game/releases/tag/v1.0.0
