from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_invalid(value: str | None) -> bool:
    return value is None or value == "None" or value == ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_user: str | None = None
    db_password: str | None = None
    db_host: str | None = None
    db_port: str | None = None
    db_name: str | None = None
    test_db_name: str | None = None
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        if any(_is_invalid(v) for v in [self.db_user, self.db_password, self.db_host, self.db_port, self.db_name]):
            return "sqlite+aiosqlite:///./test.db"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def test_database_url(self) -> str:
        if any(_is_invalid(v) for v in [self.db_user, self.db_password, self.db_host, self.db_port, self.test_db_name]):
            return "sqlite+aiosqlite:///./test.db"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.test_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
