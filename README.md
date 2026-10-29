# 🎭 The Meme Game 🎭

*Because who doesn't want to judge memes while pretending to be funny?*

## What's This All About? 🤔

Welcome to the most chaotic, hilarious, and slightly unhinged meme card game you'll ever play! Think Cards Against Humanity, but with memes and your friends' questionable sense of humor. 

Players take turns being the "judge" (we call them leaders because it sounds more important), while everyone else tries to match the perfect meme to a ridiculous situation. The best part? You get to roast your friends' choices in real-time! 🔥

## How to Play (The Rules That Matter) 🎮

1. **Gather Your Squad** 👥
   - Need at least 3 players (because 2 people judging each other gets awkward)
   - Max 10 players (because more than that is just chaos)

2. **Get Your Cards** 🃏
   - Everyone starts with 6 random meme cards
   - All cards are unique (no cheating!)
   - The room host becomes the first leader

3. **The Round Begins** ⚡
   - Leader gets a random situation card
   - Everyone else (except the leader) picks ONE meme card from their hand
   - You have 60 seconds to decide (pressure makes it funnier!)
   - Round ends when everyone picks or time runs out

4. **The Judgement** 👨‍⚖️
   - Leader picks the winner (prepare for bias and favoritism)
   - Winner gets +1 point (congrats, you're officially funny!)
   - Used meme cards go to the discard pile for 10 rounds
   - Used situation cards are gone for 20 rounds (they need a longer break)

5. **Keep the Party Going** 🔄
   - Everyone gets +1 new meme card (except the leader, they're busy judging)
   - New leader is chosen in connection order
   - Repeat until you run out of situations or your friends get tired of your jokes

6. **Clean Up** 🧹
   - When everyone leaves, the room disappears into the digital void
   - No permanent records of your terrible memes (your secret is safe!)

## Tech Stuff (For the Nerds) 💻

### What We Built
- **FastAPI** backend (because we like things fast and async)
- **WebSocket** real-time communication (no more waiting for page refreshes!)
- **In-memory game state** (because databases are for boring stuff)
- **PostgreSQL** for storing cards (the only thing we keep permanent)

### Architecture Highlights
- All game logic lives in memory (faster than a caffeinated squirrel)
- Username uniqueness per room (no "Player1" and "Player1" confusion)
- Automatic cleanup when games end (like a digital Marie Kondo)
- Real-time synchronization (everyone sees the same chaos)

### The Stack
```
Frontend: React (because we're not monsters)
Backend: FastAPI + WebSockets
Database: PostgreSQL (for the cards)
Real-time: Redis (for the chaos)
Deployment: Docker (because containers are cool)
```

## Getting Started (The Not-So-Boring Part) 🚀

### Prerequisites
- Python 3.12+ (because we like shiny new things)
- PostgreSQL (for storing our precious meme collection)
- Redis (for the real-time magic)
- Docker (optional, but recommended for the full experience)

### Installation

1. **Clone this beautiful mess**
   ```bash
   git clone https://github.com/your-username/the_meme_game.git
   cd the_meme_game
   ```

2. **Set up your environment**
   ```bash
   # Create virtual environment (because we're responsible adults)
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies (runtime + tests/linters)
   pip install -r requirements-dev.txt
   ```

3. **Configure your database**
   ```bash
   # Copy the example env file
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

5. **Start the party**
   ```bash
   # Start the FastAPI server (HTTP + WebSocket, same app, same port)
   uvicorn app.main:app --reload
   ```

6. **Open your browser and prepare for chaos**
   ```
   http://localhost:8000
   ```

## API Endpoints (For the Curious) 🔌

### Cards
- `GET /cards/meme_cards` - Get all meme cards
- `GET /cards/situation_cards` - Get all situation cards
- `POST /cards/meme_cards` - Add new meme card (admin only)
- `POST /cards/situation_cards` - Add new situation card (admin only)

### Game Logic (WebSocket)
- Create room
- Join room (with username validation)
- Start game
- Select cards
- Choose winner
- Leave room

## Contributing (We Want Your Memes!) 🤝

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-meme-addition`)
3. Add your memes (I mean, code)
4. Commit your changes (`git commit -m 'Add hilarious new feature'`)
5. Push to the branch (`git push origin feature/amazing-meme-addition`)
6. Open a Pull Request

## Game Rules (The Serious Stuff) 📋

- **Minimum Players**: 3 (because 2 is just awkward)
- **Maximum Players**: 10 (because more is chaos)
- **Cards per Player**: 6 (start), +1 each round
- **Round Time Limit**: 60 seconds
- **Meme Card Cooldown**: 10 rounds
- **Situation Card Cooldown**: 20 rounds
- **Username Uniqueness**: Per room (global usernames are overrated)

## Troubleshooting (When Things Go Wrong) 🔧

### "Room not found"
- Check if the room ID is correct
- Make sure the room hasn't been cleaned up

### "Username already exists"
- Pick a different username (be creative!)
- Usernames are case-insensitive

### "Not enough players"
- Gather more friends (or make new ones)
- Minimum 3 players required

### "No situation cards available"
- Game is over! Time to start a new one
- Or add more situation cards to the database

## License (The Legal Stuff) 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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