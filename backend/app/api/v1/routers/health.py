"""Health check endpoint for liveness and readiness.

Provides:
    - GET /health: Returns application status and database connectivity.
      Does NOT crash the process if the database is unreachable.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Report application liveness and database readiness.

    Returns 200 with:
        - status: "ok" if the application is running.
        - database: "up" if DB is reachable, "down" otherwise.
    """
    database_status = "down"
    try:
        await db.execute(text("SELECT 1"))
        database_status = "up"
    except Exception:
        logger.warning("Health check: database is not reachable", exc_info=True)

    return {
        "status": "ok",
        "database": database_status,
    }
