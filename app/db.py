import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")


def is_invalid(value):
    return value is None or value == "None" or value == ""


if any(is_invalid(v) for v in [DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, TEST_DB_NAME]):
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
else:
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=False)
session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with session_maker() as session:
        yield session


class Base(DeclarativeBase):
    pass
