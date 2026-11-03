"""Load situation texts into the game, for trying it out locally.

    python -m scripts.load_situations                 # the test situations from scripts/situations.txt
    python -m scripts.load_situations my_file.txt

One situation per line; empty lines and lines starting with # are skipped. Safe to run again:
situations already in the database are skipped.
"""

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import select

from app.db import DATABASE_URL, engine, session_maker
from app.models import SituationCard

DEFAULT_FILE = Path(__file__).resolve().parent / "situations.txt"
MAX_LENGTH = 500  # as in the card schema


async def load_situations(path: Path) -> tuple[int, int]:
    """Add the situations that aren't in the database yet. Returns (added, already there)."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    texts = list(dict.fromkeys(line for line in lines if line and not line.startswith("#")))  # no repeats, in order

    too_long = [text for text in texts if len(text) > MAX_LENGTH]
    if too_long:
        raise SystemExit(f"longer than {MAX_LENGTH} characters: {too_long[0][:60]}...")

    async with session_maker() as db:
        existing = set((await db.scalars(select(SituationCard.text))).all())
        new = [text for text in texts if text not in existing]
        db.add_all(SituationCard(text=text) for text in new)
        await db.commit()

    return len(new), len(texts) - len(new)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, nargs="?", default=DEFAULT_FILE, help="text file, one situation per line")
    args = parser.parse_args()
    path = args.file.expanduser()

    if not path.is_file():
        parser.error(f"no such file: {path}")

    async def run():
        try:
            return await load_situations(path)
        finally:
            await engine.dispose()

    print(f"database: {DATABASE_URL.split('@')[-1]}")  # without the password
    added, skipped = asyncio.run(run())
    print(f"added {added} situations, {skipped} were already there")


if __name__ == "__main__":
    main()
