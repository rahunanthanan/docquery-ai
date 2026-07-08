"""Async SQLAlchemy engine, session factory and FastAPI session dependency.

Declared in Task 2 so every later module shares one session pattern; the
first real models and Alembic migrations arrive with auth (Task 3), so
nothing here opens a connection until a request actually uses the
dependency.
"""

from collections.abc import AsyncIterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base all ORM models inherit from."""

    # §5 uses timestamptz everywhere
    type_annotation_map = {datetime: DateTime(timezone=True)}


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    if settings.environment == "test":
        # TestClient runs each test in a fresh event loop; pooled asyncpg
        # connections are loop-bound, so tests must not reuse them.
        return create_async_engine(settings.database_url, poolclass=NullPool)
    return create_async_engine(settings.database_url)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding one session per request."""
    async with get_sessionmaker()() as session:
        yield session
