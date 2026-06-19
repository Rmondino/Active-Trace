"""FastAPI dependencies for current user resolution from JWT.

Provides:
    - get_current_user: extracts JWT, verifies, resolves User from DB
    - get_current_user_impersonable: requires impersonacion:usar permission
    - get_current_user_impersonating: requires impersonando=True in JWT
    - require_2fa: gates endpoints for users who must complete 2FA
"""

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.jwt import verify_token
from app.models.user import User
from app.services.permission_service import PermissionService


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    """FastAPI dependency: resolve the current user from a JWT."""
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
            detail="Token invalido o expirado",
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


async def get_current_user_impersonable(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency: require impersonacion:usar permission."""
    ps = PermissionService(db)
    has_perm = await ps.has_permission(current_user, "impersonacion:usar")
    if not has_perm:
        raise HTTPException(
            status_code=403,
            detail="Permiso requerido: impersonacion:usar",
        )
    return current_user


async def get_current_user_impersonating(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    request: Request = None,
) -> User:
    """FastAPI dependency: require impersonando=True in JWT."""
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
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not claims.get("impersonando"):
        raise HTTPException(
            status_code=403,
            detail="Se requiere una sesion de impersonacion activa",
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token sin identidad",
            headers={"WWW-Authenticate": "Bearer"},
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

    request.state.actor_original_id = claims.get("actor_original_id")
    request.state.impersonando = True
    return user


async def require_2fa(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: ensure the user has completed 2FA."""
    if not current_user.two_fa_enabled:
        raise HTTPException(
            status_code=403,
            detail="2FA requerido para esta operacion",
        )
    return current_user
