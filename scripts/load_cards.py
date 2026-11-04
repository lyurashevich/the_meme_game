"""Load cards into the game: meme pictures from a folder, situations from a text file.

    python -m scripts.load_cards memes ~/Загрузки/memegen_memes
    python -m scripts.load_cards situations                    # the test ones from scripts/situations.txt
    python -m scripts.load_cards situations my_situations.txt

Memes: every picture in the folder (and its subfolders) is copied to the media folder (MEDIA_DIR) under
a name made from its content, e.g. memes/3f9a1c0b7d2e4a51.jpg, and a card with that key is added.
The same picture under two names is one card; files that aren't pictures are skipped and named.

Situations: one per line; empty lines and lines starting with # are skipped.

Safe to run again: what is already there is skipped.
"""

import argparse
import asyncio
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.models import MemeCard, SituationCard

MEMES_FOLDER = "memes"  # inside the media folder; the keys start with it
SITUATIONS_FILE = Path(__file__).resolve().parent / "situations.txt"
MAX_SITUATION_LENGTH = 500  # as in the card schema

# How each kind of picture starts. The first bytes are checked, not the file's extension, which can be
# anything: a .jpg may well be a PNG, a "picture" may be a web page saved by mistake.
_SIGNATURES = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
]


def picture_type(data: bytes) -> str | None:
    """The extension for this kind of picture (jpg, png, gif, webp), or None if it isn't one."""
    for signature, extension in _SIGNATURES:
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":  # RIFF, then the size, then the format
        return "webp"
    return None


def image_key(data: bytes, extension: str) -> str:
    """memes/<the start of the content's SHA-256>.<extension>.

    The same picture always gets the same name, and a different one a different name, so a picture
    never changes under its address (nginx lets browsers keep them for a month).
    16 hex digits (64 bits) are plenty: two different pictures sharing them is practically impossible.
    """
    return f"{MEMES_FOLDER}/{hashlib.sha256(data).hexdigest()[:16]}.{extension}"


@dataclass
class MemesReport:
    added: int = 0
    already_there: int = 0
    duplicates: list[Path] = field(default_factory=list)  # the same picture as another file in the folder
    not_pictures: list[Path] = field(default_factory=list)
    old_addresses: int = 0  # cards loaded before keys, with whole addresses (see the hint in main)


@dataclass
class SituationsReport:
    added: int = 0
    already_there: int = 0


async def load_memes(session_factory, source: Path, media_dir: Path) -> MemesReport:
    report = MemesReport()
    files = sorted(p for p in source.rglob("*") if p.is_file() and not p.name.startswith("."))

    async with session_factory() as db:
        existing = set((await db.scalars(select(MemeCard.image_key))).all())
        seen: set[str] = set()  # the keys of this run

        for path in files:
            data = path.read_bytes()
            extension = picture_type(data)
            if extension is None:
                report.not_pictures.append(path)
                continue

            key = image_key(data, extension)
            if key in seen:
                report.duplicates.append(path)
                continue
            seen.add(key)

            _save(media_dir / key, data)  # also when the card is there: the file may have been lost
            if key in existing:
                report.already_there += 1
            else:
                db.add(MemeCard(image_key=key))
                report.added += 1

        report.old_addresses = await db.scalar(
            select(func.count()).select_from(MemeCard).where(MemeCard.image_key.like("http%"))
        )
        await db.commit()

    return report


def _save(target: Path, data: bytes) -> None:
    """Write the file unless it is there. Through a temporary file, so that an interrupted run never
    leaves half a picture under the real name (nginx would give it out as it is)."""
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, target)  # instant: the name points either to nothing or to the whole file


def read_situations(path: Path) -> list[str]:
    """The situations from the file: no empty lines, comments or repeats, in the file's order."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    texts = list(dict.fromkeys(line for line in lines if line and not line.startswith("#")))
    too_long = [text for text in texts if len(text) > MAX_SITUATION_LENGTH]
    if too_long:
        raise ValueError(f"longer than {MAX_SITUATION_LENGTH} characters: {too_long[0][:60]}...")
    return texts


async def load_situations(session_factory, path: Path) -> SituationsReport:
    texts = read_situations(path)

    async with session_factory() as db:
        existing = set((await db.scalars(select(SituationCard.text))).all())
        new = [text for text in texts if text not in existing]
        db.add_all(SituationCard(text=text) for text in new)
        await db.commit()

    return SituationsReport(added=len(new), already_there=len(texts) - len(new))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    memes = commands.add_parser("memes", help="pictures from a folder")
    memes.add_argument("source", type=Path, help="folder with the pictures")
    memes.add_argument("--media-dir", type=Path, help="where to copy them (default: MEDIA_DIR)")

    situations = commands.add_parser("situations", help="texts from a file, one per line")
    situations.add_argument("file", type=Path, nargs="?", default=SITUATIONS_FILE, help="default: %(default)s")

    args = parser.parse_args()
    if args.command == "memes":
        args.source = args.source.expanduser()
        if not args.source.is_dir():
            parser.error(f"not a folder: {args.source}")
    else:
        args.file = args.file.expanduser()
        if not args.file.is_file():
            parser.error(f"no such file: {args.file}")
    return args


def main() -> None:
    args = _parse_args()
    from app.db import (  # here: --help works without a database
        DATABASE_URL,
        engine,
        session_maker,
    )

    print(f"database: {DATABASE_URL.split('@')[-1]}")  # without the password

    async def run():
        try:
            if args.command == "memes":
                media_dir = (args.media_dir or get_settings().media_dir).expanduser()
                print(f"pictures go to: {media_dir}")
                return await load_memes(session_maker, args.source, media_dir)
            return await load_situations(session_maker, args.file)
        finally:
            await engine.dispose()

    try:
        report = asyncio.run(run())
    except ValueError as error:
        raise SystemExit(f"error: {error}")

    if isinstance(report, SituationsReport):
        print(f"added {report.added} situations, {report.already_there} were already there")
        return

    print(f"added {report.added} memes, {report.already_there} were already there")
    if report.duplicates:
        print(f"{len(report.duplicates)} files are the same picture as another one, skipped:")
        print("".join(f"  {path}\n" for path in report.duplicates), end="")
    if report.not_pictures:
        print(f"{len(report.not_pictures)} files aren't pictures (jpg, png, gif, webp), skipped:")
        print("".join(f"  {path}\n" for path in report.not_pictures), end="")
    if report.old_addresses:
        print(
            f"\nnote: {report.old_addresses} cards have whole addresses from the old loading script; if the same "
            "pictures were loaded now, the deck has them twice. To remove the old ones:\n"
            "  DELETE FROM meme_cards WHERE image_key LIKE 'http%';"
        )


if __name__ == "__main__":
    main()
