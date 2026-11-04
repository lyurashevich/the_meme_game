"""meme_cards: keep the image key instead of the whole address

The address is now built from MEDIA_BASE_URL and the key, so moving the pictures means changing one
setting. Cards loaded before keep their whole addresses in the column; those are given out as they are.

Revision ID: 5b8e2f6a9c13
Revises: 461fd21c9b21
Create Date: 2026-11-04 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b8e2f6a9c13"
down_revision: Union[str, Sequence[str], None] = "461fd21c9b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("meme_cards", "image_url", new_column_name="image_key")
    op.create_unique_constraint("uq_meme_cards_image_key", "meme_cards", ["image_key"])


def downgrade() -> None:
    op.drop_constraint("uq_meme_cards_image_key", "meme_cards", type_="unique")
    op.alter_column("meme_cards", "image_key", new_column_name="image_url")
