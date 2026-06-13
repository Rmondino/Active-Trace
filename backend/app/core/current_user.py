"""FastAPI dependencies for current user resolution from JWT.

Provides:
    - get_current_user: extracts JWT, verifies, resolves User from DB
    - require_2fa: gates endpoints for users who must complete 2FA
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.jwt import verify_token
from app.models.user import User


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    """FastAPI dependency: resolve the current user from a JWT.

    Extracts the Bearer token from the Authorization header, verifies it,
    and fetches the corresponding User from the database.

    Args:
        authorization: The Authorization header value ("Bearer <token>").
        db: Database session.
        settings: App settings.

    Returns:
        The authenticated User.

    Raises:
        HTTPException 401 if the token is missing, invalid, expired,
        or the user is not found / soft-deleted.
        HTTPException 403 if the token lacks a tenant_id claim.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token de acceso requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    claims = verify_token(token, settings)
    if claims is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token sin identidad",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if "tenant_id" not in claims:
        raise HTTPException(
            status_code=403,
            detail="Token sin tenant",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_2fa(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: ensure the user has completed 2FA.

    Use on endpoints that require 2FA to be active.

    Args:
        current_user: The authenticated user.

    Returns:
        The same user if 2FA is enabled.

    Raises:
        HTTPException 403 if 2FA is not enabled for this user.
    """
    if not current_user.two_fa_enabled:
        raise HTTPException(
            status_code=403,
            detail="2FA requerido para esta operación",
        )
    return current_user
