from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.media import media_url


class MemeCard(Base):
    __tablename__ = "meme_cards"
    # Named as in the migration, so the tests' tables (create_all) match the real ones
    __table_args__ = (UniqueConstraint("image_key", name="uq_meme_cards_image_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Where the picture is among the media files, e.g. "memes/3f9a1c.jpg"; unique, so a picture
    # can't get into the deck twice
    image_key: Mapped[str] = mapped_column(String, nullable=False)

    @property
    def image_url(self) -> str:
        """The address the browser loads the picture from (MEDIA_BASE_URL + the key)."""
        return media_url(self.image_key)

    def to_dict(self):
        return {"id": self.id, "image_key": self.image_key, "image_url": self.image_url}


class SituationCard(Base):
    __tablename__ = "situation_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "text": self.text}
