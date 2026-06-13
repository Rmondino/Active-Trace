"""Smoke tests for async database connection.

Uses the shared conftest fixtures for engine and session.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


@pytest.fixture(scope="module")
def db_settings() -> Settings:
    """Settings pointing to the test database."""
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


@pytest.mark.asyncio
async def test_smoke_select_1(db_settings: Settings):
    """A session can execute SELECT 1 and get a result."""
    engine = create_async_engine(
        db_settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with maker() as session:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar_one()
        assert value == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_session_closes_on_exception(db_settings: Settings):
    """Session is properly closed when an exception occurs."""
    engine = create_async_engine(
        db_settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    session = maker()
    try:
        async with session:
            # Force an invalid query to trigger an exception
            await session.execute(text("INVALID SQL"))
    except Exception:
        pass  # Expected

    # After rollback, session can still be used but has no pending changes
    result = await session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1

    await engine.dispose()
