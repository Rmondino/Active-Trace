"""Impersonation router — iniciar/dejar impersonación con JWT especial.

All endpoints require impersonacion:usar permission.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import (
    get_current_user,
    get_current_user_impersonable,
    get_current_user_impersonating,
)
from app.core.dependencies import get_db
from app.core.jwt import create_access_token
from app.models.user import User
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ImpersonarRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    usuario_id: str


@router.post("/impersonar")
async def impersonar(
    body: ImpersonarRequest,
    current_user: User = Depends(get_current_user_impersonable),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Start impersonating another user in the same tenant.

    Requires impersonacion:usar permission.
    Returns a JWT with impersonando=True and actor_original_id.
    """
    result = await db.execute(
        select(User).where(
            User.id == body.usuario_id,
            User.tenant_id == current_user.tenant_id,
            User.deleted_at.is_(None),
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    access_token = create_access_token(
        user=target,
        settings=settings,
        impersonando=True,
        actor_original_id=current_user.id,
    )

    audit = AuditLogService(db)
    await audit.log(
        actor_id=current_user.id,
        tenant_id=current_user.tenant_id,
        accion="IMPERSONACION_INICIAR",
        detalle={"usuario_impersonado": target.id},
        impersonado_id=target.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "impersonando": True,
    }


@router.post("/dejar-impersonar")
async def dejar_impersonar(
    current_user: User = Depends(get_current_user_impersonating),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Stop impersonating and restore original session.

    Requires an active impersonation JWT.
    """
    actor_original_id: str | None = getattr(request.state, "actor_original_id", None)
    if not actor_original_id:
        raise HTTPException(status_code=403, detail="No hay sesión de impersonación activa")

    result = await db.execute(
        select(User).where(
            User.id == actor_original_id,
            User.deleted_at.is_(None),
        )
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Usuario original no encontrado")

    access_token = create_access_token(
        user=original,
        settings=settings,
        impersonando=False,
    )

    audit = AuditLogService(db)
    await audit.log(
        actor_id=original.id,
        tenant_id=original.tenant_id,
        accion="IMPERSONACION_FINALIZAR",
        detalle={"usuario_impersonado": current_user.id},
        impersonado_id=current_user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "impersonando": False,
    }
