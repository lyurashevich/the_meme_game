"""
Database initialization script
Run this to create all tables in the database
"""

import asyncio

from app.db import Base, engine


async def init_db():
    """Create all database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
