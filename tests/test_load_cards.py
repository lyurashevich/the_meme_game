"""The card loading script: pictures into the media folder and keys into the database; situations."""

import pytest
from sqlalchemy import select

from app.models import MemeCard, SituationCard
from scripts.load_cards import (
    SITUATIONS_FILE,
    image_key,
    load_memes,
    load_situations,
    picture_type,
    read_situations,
)

JPEG = b"\xff\xd8\xff\xe0" + b"a jpeg picture"
PNG = b"\x89PNG\r\n\x1a\n" + b"a png picture"
GIF = b"GIF89a" + b"a gif picture"
WEBP = b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"a webp picture"


@pytest.fixture
def folder(tmp_path):
    """The folder the pictures are loaded from."""
    source = tmp_path / "source"
    source.mkdir()
    return source


@pytest.fixture
def media_dir(tmp_path):
    return tmp_path / "media"


@pytest.fixture
def load(db_session, session_factory, folder, media_dir):
    async def load():
        return await load_memes(session_factory, folder, media_dir)

    return load


async def card_keys(db_session):
    db_session.expire_all()
    return sorted((await db_session.scalars(select(MemeCard.image_key))).all())


class TestPictureType:
    @pytest.mark.parametrize("data, expected", [(JPEG, "jpg"), (PNG, "png"), (GIF, "gif"), (WEBP, "webp")])
    def test_known_pictures(self, data, expected):
        assert picture_type(data) == expected

    @pytest.mark.parametrize("data", [b"", b"<html>a saved page</html>", b"RIFF\x10\x00\x00\x00WAVEfmt "])
    def test_anything_else(self, data):
        assert picture_type(data) is None


class TestImageKey:
    def test_comes_from_the_content(self):
        assert image_key(JPEG, "jpg") == image_key(JPEG, "jpg")
        assert image_key(JPEG, "jpg") != image_key(JPEG + b"!", "jpg")

    def test_shape(self):
        key = image_key(JPEG, "jpg")
        folder, name = key.split("/")
        assert folder == "memes"
        assert len(name) == len("0123456789abcdef.jpg")


class TestLoadMemes:
    async def test_copies_the_pictures_and_adds_their_cards(self, load, folder, media_dir, db_session):
        (folder / "кот мем.jpg").write_bytes(JPEG)
        (folder / "sub").mkdir()
        (folder / "sub" / "dog.png").write_bytes(PNG)

        report = await load()

        assert report.added == 2
        keys = await card_keys(db_session)
        assert sorted([image_key(JPEG, "jpg"), image_key(PNG, "png")]) == keys
        assert (media_dir / image_key(JPEG, "jpg")).read_bytes() == JPEG
        assert (media_dir / image_key(PNG, "png")).read_bytes() == PNG

    async def test_running_again_adds_nothing(self, load, folder, db_session):
        (folder / "a.jpg").write_bytes(JPEG)
        await load()

        report = await load()

        assert (report.added, report.already_there) == (0, 1)
        assert len(await card_keys(db_session)) == 1

    async def test_new_pictures_are_added_on_the_next_run(self, load, folder, db_session):
        (folder / "a.jpg").write_bytes(JPEG)
        await load()
        (folder / "b.png").write_bytes(PNG)

        report = await load()

        assert (report.added, report.already_there) == (1, 1)

    async def test_the_same_picture_under_two_names_is_one_card(self, load, folder, db_session):
        (folder / "a.jpg").write_bytes(JPEG)
        (folder / "a copy.jpg").write_bytes(JPEG)

        report = await load()

        assert report.added == 1
        assert report.duplicates == [folder / "a.jpg"]  # sorted: "a copy.jpg" comes first
        assert len(await card_keys(db_session)) == 1

    async def test_the_extension_comes_from_the_content(self, load, folder, db_session):
        (folder / "actually a png.jpg").write_bytes(PNG)

        await load()

        assert await card_keys(db_session) == [image_key(PNG, "png")]

    async def test_files_that_arent_pictures_are_skipped(self, load, folder, media_dir, db_session):
        (folder / "a.jpg").write_bytes(JPEG)
        (folder / "notes.txt").write_text("not a picture")
        (folder / "page.jpg").write_bytes(b"<html></html>")
        (folder / ".DS_Store").write_bytes(b"\x00")  # hidden: not even reported

        report = await load()

        assert report.added == 1
        assert report.not_pictures == [folder / "notes.txt", folder / "page.jpg"]
        assert [p.name for p in (media_dir / "memes").iterdir()] == [image_key(JPEG, "jpg").split("/")[1]]

    async def test_a_lost_file_is_copied_again(self, load, folder, media_dir):
        (folder / "a.jpg").write_bytes(JPEG)
        await load()
        (media_dir / image_key(JPEG, "jpg")).unlink()

        await load()

        assert (media_dir / image_key(JPEG, "jpg")).read_bytes() == JPEG

    async def test_leaves_no_temporary_files(self, load, folder, media_dir):
        (folder / "a.jpg").write_bytes(JPEG)

        await load()

        assert [p.name for p in (media_dir / "memes").iterdir() if p.name.startswith(".")] == []

    async def test_counts_the_cards_with_old_whole_addresses(self, load, folder, db_session):
        db_session.add(MemeCard(image_key="http://localhost:5173/memes/a.jpg"))
        await db_session.commit()
        (folder / "a.jpg").write_bytes(JPEG)

        report = await load()

        assert report.old_addresses == 1


class TestLoadSituations:
    async def test_adds_the_new_ones_once(self, db_session, session_factory, tmp_path):
        path = tmp_path / "situations.txt"
        path.write_text("# a comment\nfirst\n\n  second  \nfirst\n", encoding="utf-8")

        first = await load_situations(session_factory, path)
        again = await load_situations(session_factory, path)

        assert (first.added, first.already_there) == (2, 0)
        assert (again.added, again.already_there) == (0, 2)
        texts = (await db_session.scalars(select(SituationCard.text).order_by(SituationCard.id))).all()
        assert texts == ["first", "second"]

    def test_too_long_is_an_error(self, tmp_path):
        path = tmp_path / "situations.txt"
        path.write_text("x" * 501, encoding="utf-8")

        with pytest.raises(ValueError, match="longer than 500"):
            read_situations(path)

    def test_the_test_situations_are_fine(self):
        assert len(read_situations(SITUATIONS_FILE)) >= 21
