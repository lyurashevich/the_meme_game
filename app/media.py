"""Turning a meme card's image key into the address the browser loads the picture from.

The database keeps only the key, e.g. "memes/3f9a1c.jpg"; where the pictures are served from is
MEDIA_BASE_URL. Moving the pictures (another domain, a storage service) means changing one setting,
not every card in the database.
"""

from urllib.parse import quote

from app.config import get_settings

# Keys that are already whole addresses, from before there were keys: given out as they are
_ADDRESS_PREFIXES = ("http://", "https://", "/")


def media_url(image_key: str, base_url: str | None = None) -> str:
    if image_key.startswith(_ADDRESS_PREFIXES):
        return image_key
    if base_url is None:
        base_url = get_settings().media_base_url
    return f"{base_url.rstrip('/')}/{quote(image_key)}"
