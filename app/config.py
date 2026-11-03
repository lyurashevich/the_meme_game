from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Both are found from the project root, wherever the app is started from (PyCharm, a script, tests).
# Starting it from another folder used to miss .env and quietly create an empty SQLite file there.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'test.db'}"


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

    @property
    def database_url(self) -> str:
        if any(_is_invalid(v) for v in [self.db_user, self.db_password, self.db_host, self.db_port, self.db_name]):
            return SQLITE_URL
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def test_database_url(self) -> str:
        if any(_is_invalid(v) for v in [self.db_user, self.db_password, self.db_host, self.db_port, self.test_db_name]):
            return SQLITE_URL
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.test_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
