from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url
TEST_DATABASE_URL = settings.test_database_url

engine = create_async_engine(DATABASE_URL, echo=False)
session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with session_maker() as session:
        yield session


class Base(DeclarativeBase):
    pass
