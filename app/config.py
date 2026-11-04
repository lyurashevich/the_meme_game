from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env is found from the project root, wherever the app is started from (PyCharm, a script, tests)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DatabaseNotConfiguredError(RuntimeError):
    """PostgreSQL settings are missing. Raised at startup, instead of quietly using some other database."""


def _is_invalid(value: str | None) -> bool:
    return value is None or value == "None" or value == ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    db_user: str | None = None
    db_password: str | None = None
    db_host: str | None = None
    db_port: str | None = None
    db_name: str | None = None
    test_db_name: str | None = None
    log_level: str = "INFO"
    # Enables the card editing endpoints (POST/PATCH/DELETE /api/memes, /api/situations) for requests
    # with a matching X-Admin-Token header. Not set: those endpoints are disabled.
    admin_token: str | None = None
    # Where the browser loads the meme pictures from; a card's address is this plus its image key.
    # Relative by default: the pictures come from the same site as the game, wherever it runs.
    media_base_url: str = "/media"
    # Where the meme pictures are kept as files: media/ in the project root; /media in docker-compose.
    # The card loading script copies the pictures here; Vite or nginx gives them out at MEDIA_BASE_URL.
    media_dir: Path = PROJECT_ROOT / "media"

    @property
    def database_url(self) -> str:
        return self._postgres_url(self.db_name, "DB_NAME")

    @property
    def test_database_url(self) -> str:
        """The database pytest uses; it is wiped by the tests, so never the one with real data."""
        return self._postgres_url(self.test_db_name, "TEST_DB_NAME")

    def _postgres_url(self, db_name: str | None, db_name_variable: str) -> str:
        values = {
            "DB_HOST": self.db_host,
            "DB_PORT": self.db_port,
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
            db_name_variable: db_name,
        }
        missing = [variable for variable, value in values.items() if _is_invalid(value)]
        if missing:
            raise DatabaseNotConfiguredError(
                f"PostgreSQL is not configured: set {', '.join(missing)} in .env or in the environment "
                "(see .env.example)"
            )
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
