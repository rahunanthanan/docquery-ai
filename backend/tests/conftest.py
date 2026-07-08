"""Shared fixtures: an isolated `docquery_test` database, migrated via Alembic.

Requires a reachable Postgres — the compose `db` service locally, or the
pgvector service container in CI. The test database is dropped and
recreated once per session, and tables are truncated after every test.
"""

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

# Must be set before any app import so the cached Settings pick them up.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://docquery:docquery@localhost:5432/docquery_test"
)
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-padded-to-32b")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.main import create_app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB_URL = os.environ["DATABASE_URL"]
_SERVER_URL, _TEST_DB_NAME = TEST_DB_URL.rsplit("/", 1)
_ADMIN_URL = f"{_SERVER_URL}/postgres"


async def _recreate_database() -> None:
    engine = create_async_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{_TEST_DB_NAME}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{_TEST_DB_NAME}"'))
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _database() -> Iterator[None]:
    asyncio.run(_recreate_database())
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    yield


async def _truncate_all() -> None:
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE users CASCADE"))
    await engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    asyncio.run(_truncate_all())


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client
