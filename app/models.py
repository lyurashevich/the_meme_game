from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MemeCard(Base):
    __tablename__ = "meme_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_url: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "image_url": self.image_url}


class SituationCard(Base):
    __tablename__ = "situation_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self):
        return {"id": self.id, "text": self.text}
