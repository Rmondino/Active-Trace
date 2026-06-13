"""Tests for application startup (RED → GREEN).

Verifies that the FastAPI application can be created and runs without errors.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.database import init_engine


@pytest.fixture
def test_settings() -> Settings:
    """Settings for startup tests."""
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/nonexistent_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestAppStartup:
    """Application startup smoke tests."""

    @pytest.mark.asyncio
    async def test_app_creates_without_error(self, test_settings: Settings):
        """The FastAPI app can be created (lifespan) without error (RED → GREEN)."""
        from app.main import create_app  # noqa: PLC0415

        # This should not raise
        app = create_app(settings=test_settings)
        assert app is not None
        assert app.title == "activia-trace"

    @pytest.mark.asyncio
    async def test_app_starts_and_serves_requests(self, test_settings: Settings):
        """The app starts and can serve requests via ASGI (GREEN)."""
        from app.main import create_app  # noqa: PLC0415

        init_engine(test_settings)
        app = create_app(settings=test_settings)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
