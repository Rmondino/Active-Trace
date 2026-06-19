"""Async database engine and session management for SQLAlchemy 2.0 + asyncpg.

Provides:
- Engine: single async engine created at application startup.
- Session factory: async_sessionmaker for creating per-request sessions.
- Base: declarative base for ORM models.
- get_db_session: FastAPI dependency that yields a session and closes it on exit.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Domain models typically inherit from Base plus one or more mixins:
        - TimeStampedMixin  → created_at / updated_at
        - SoftDeleteMixin   → deleted_at (nullable, soft delete)
        - TenantScopedMixin → tenant_id FK (multi-tenant isolation)

    Example:
        class MyModel(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
            __tablename__ = "my_model"
            ...
    """


_engine = None
_async_session_maker = None


def init_engine(settings: Settings) -> None:
    """Create the async engine from application Settings.

    Idempotent: can be called multiple times (replaces the engine).
    Must be called before any database operation.
    """
    global _engine, _async_session_maker  # noqa: PLW0603
    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_engine() -> None:
    """Dispose of the async engine.

    Must be called during application shutdown.
    """
    global _engine, _async_session_maker  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _async_session_maker = None


def get_session_maker():
    """Return the current session maker (used in tests)."""
    if _async_session_maker is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session per request.

    The session is automatically closed when the request finishes,
    even if an exception occurs.
    """
    maker = get_session_maker()
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
