"""Load meme pictures from a folder into the game, for trying it out locally.

    python -m scripts.load_memes ~/Загрузки/memegen_memes

The pictures are copied to frontend/public/memes (the Vite dev server serves that folder), and a card
is added to the database for each one, with the address the browser will load it from. Safe to run
again: pictures already in the database are skipped.

Not for production: there the pictures belong in a media storage (see "Контент" in docs/mvp-plan.md).
"""

import argparse
import asyncio
import shutil
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select

from app.db import DATABASE_URL, engine, session_maker
from app.models import MemeCard

PICTURE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
TARGET_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "memes"
DEFAULT_BASE_URL = "http://localhost:5173/memes"  # the Vite dev server


async def load_memes(source: Path, target: Path, base_url: str) -> tuple[int, int]:
    """Copy the pictures and add the missing cards. Returns (added, already there)."""
    pictures = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in PICTURE_SUFFIXES)
    target.mkdir(parents=True, exist_ok=True)

    async with session_maker() as db:
        existing = set((await db.scalars(select(MemeCard.image_url))).all())
        added = 0
        for picture in pictures:
            url = f"{base_url.rstrip('/')}/{quote(picture.name)}"  # names have spaces and the like
            shutil.copy2(picture, target / picture.name)
            if url not in existing:
                db.add(MemeCard(image_url=url))
                added += 1
        await db.commit()

    return added, len(pictures) - added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="folder with the pictures")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"where the browser loads them from ({DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()
    source = args.source.expanduser()

    if not source.is_dir():
        parser.error(f"not a folder: {source}")

    async def run():
        try:
            return await load_memes(source, TARGET_DIR, args.base_url)
        finally:
            await engine.dispose()

    print(f"database: {DATABASE_URL.split('@')[-1]}")  # without the password
    added, skipped = asyncio.run(run())
    print(f"added {added} memes, {skipped} were already there; pictures are in {TARGET_DIR}")


if __name__ == "__main__":
    main()
