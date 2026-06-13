"""Tests for GET /health endpoint.

RED → GREEN → TRIANGULATE:
    - RED:   Expect 200 + JSON with status field
    - GREEN: Implement the endpoint
    - TRIANGULATE: Database down case (no real DB → database reports "down")
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.database import init_engine


@pytest.fixture
def test_settings() -> Settings:
    """Settings for health tests (no real DB needed)."""
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/nonexistent_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestHealthEndpoint:
    """Health endpoint smoke tests."""

    @pytest.mark.asyncio
    async def test_health_returns_200_with_status(self, test_settings: Settings):
        """GET /health returns 200 with JSON body containing 'status' field (RED)."""
        from app.main import create_app  # noqa: PLC0415

        init_engine(test_settings)
        app = create_app(settings=test_settings)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_has_database_field(self, test_settings: Settings):
        """GET /health includes a 'database' field (TRIANGULATE).

        Without a real DB, database reports "down" gracefully.
        """
        from app.main import create_app  # noqa: PLC0415

        init_engine(test_settings)
        app = create_app(settings=test_settings)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        body = response.json()
        assert "database" in body
        # Without a real DB connection, database should report "down"
        assert body["database"] == "down"
