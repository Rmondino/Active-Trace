"""Shared fixtures for all backend tests.

Provides:
    - test_settings: Settings instance pointing to the test database.
    - async_engine: SQLAlchemy async engine for test DB lifecycle.
    - db_session: AsyncSession connected to the test database.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.database import Base, init_engine, get_db_session


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide Settings configured for the test database."""
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


@pytest_asyncio.fixture
async def async_engine(test_settings: Settings):
    """Create a dedicated engine for test DB lifecycle (function-scoped for loop safety)."""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async session for each test."""
    maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the FastAPI app via ASGI.

    Overrides get_settings to return test_settings for the app lifetime.
    Initializes the engine with the test database URL.
    """
    from app.core.config import get_settings
    from app.main import create_app

    init_engine(test_settings)
    app = create_app()

    # Override the settings dependency for all requests
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
