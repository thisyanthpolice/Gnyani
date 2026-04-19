"""
SQLAlchemy async database engine & session factory.

Prerequisites:
  - PostgreSQL running on localhost:5432
  - Database "ragchatbot" created:
      CREATE DATABASE ragchatbot;
  - Credentials set in .env (see .env.example)
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings

# Async engine — uses asyncpg driver
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
