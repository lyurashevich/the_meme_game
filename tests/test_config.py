"""Only PostgreSQL: without its settings the app stops with a clear error.

Before: missing settings quietly switched the app to an SQLite file test.db - the same file the
tests wiped - so the app could run for a while on an empty database nobody meant to use.
"""

import pytest

from app.config import DatabaseNotConfiguredError, Settings

FULL = {
    "db_host": "localhost",
    "db_port": "5432",
    "db_user": "meme",
    "db_password": "secret",
    "db_name": "meme_game",
    "test_db_name": "meme_game_test",
}


def settings(**changes) -> Settings:
    # _env_file=None: don't read the developer's .env, only what the test gives
    return Settings(_env_file=None, **{**FULL, **changes})


def test_builds_the_postgres_address():
    assert settings().database_url == "postgresql+asyncpg://meme:secret@localhost:5432/meme_game"


def test_the_tests_get_their_own_database():
    assert settings().test_database_url == "postgresql+asyncpg://meme:secret@localhost:5432/meme_game_test"


@pytest.mark.parametrize("missing", ["db_host", "db_port", "db_user", "db_password", "db_name"])
@pytest.mark.parametrize("empty", [None, "", "None"])
def test_a_missing_setting_is_named_in_the_error(missing, empty):
    with pytest.raises(DatabaseNotConfiguredError, match=missing.upper()):
        settings(**{missing: empty}).database_url


def test_lists_everything_that_is_missing(monkeypatch):
    for variable in ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]:
        monkeypatch.delenv(variable, raising=False)  # set where the tests run (CI, Docker)

    with pytest.raises(DatabaseNotConfiguredError) as error:
        Settings(_env_file=None).database_url

    assert "DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME" in str(error.value)


def test_no_test_database_is_an_error_too():
    """Falling back to the main database would let the tests wipe it."""
    with pytest.raises(DatabaseNotConfiguredError, match="TEST_DB_NAME"):
        settings(test_db_name="").test_database_url
