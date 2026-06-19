"""FastAPI application factory for activia-trace.

Uses a factory pattern (create_app) so tests can inject Settings.
The module-level 'app' is created lazily for uvicorn/ASGI serving.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings
from app.core.database import close_engine, init_engine

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional Settings instance. If omitted, loads from environment.

    Returns:
        Configured FastAPI application ready to serve requests.
    """
    resolved_settings = settings if settings is not None else Settings()  # type: ignore[call-arg]

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan: init engine on start, dispose on shutdown."""
        from app.core.logging import configure_json_logging  # noqa: PLC0415
        from app.core.observability import init_opentelemetry  # noqa: PLC0415

        # Configure observability
        configure_json_logging()
        init_opentelemetry(resolved_settings)

        # Initialize database engine
        logger.info("Initializing database engine...")
        init_engine(resolved_settings)
        logger.info("Database engine initialized")

        yield

        # Shutdown
        logger.info("Shutting down database engine...")
        await close_engine()
        logger.info("Database engine disposed")

    app = FastAPI(
        title="activia-trace",
        description="Plataforma de gestión académica y trazabilidad multi-tenant",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register routers
    from app.api.v1.routers.health import router as health_router  # noqa: PLC0415
    from app.routers.auth import router as auth_router  # noqa: PLC0415
    from app.routers.admin.estructura import router as estructura_router  # noqa: PLC0415

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(estructura_router)

    return app
