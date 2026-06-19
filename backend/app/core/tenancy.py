"""Tenant resolution and isolation for multi-tenant support.

In C-02, the tenant_id is resolved from a placeholder (default tenant).
In C-03, this is updated to derive tenant_id from JWT claims when available.
In C-04, RBAC will add permission-level tenant scoping.

The tenant_id is injected as a FastAPI dependency and flows to
BaseRepository for automatic row-level filtering.

Resolution order:
    1. If the Authorization header contains a valid JWT → tenant_id from claims
    2. Otherwise → first active tenant in DB (fallback for anonymous endpoints)
"""

import logging
import uuid

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


async def resolve_tenant_id(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> str:
    """Resolve the current tenant_id from the request context.

    Priority:
        1. JWT claims (if Authorization header has a valid Bearer token)
        2. First active tenant in DB (fallback for anonymous/public endpoints)

    Args:
        request: The incoming HTTP request.
        db: Database session.

    Returns:
        The tenant_id (UUID as string) for the current request.
    """
    # 1. Try to extract tenant_id from JWT
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            from app.core.jwt import verify_token  # noqa: PLC0415

            claims = verify_token(token)
            if claims and "tenant_id" in claims:
                return claims["tenant_id"]
        except Exception:
            logger.debug("Could not extract tenant_id from JWT, falling back")

    # 2. Fallback: first active tenant
    tenant_id = await _resolve_default_tenant(db)
    return tenant_id


async def _resolve_default_tenant(db: AsyncSession) -> str:
    """Get the first active tenant's ID as a fallback."""
    result = await db.execute(
        select(Tenant.id).where(Tenant.estado == "Activo").limit(1)
    )
    tenant_id = result.scalar_one_or_none()
    if tenant_id is None:
        logger.warning("No active tenant found — using default tenant_id")
        return str(uuid.uuid4())
    return str(tenant_id)


# Re-exported from dependencies.py for discoverability
get_tenant = resolve_tenant_id
