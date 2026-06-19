"""Admin auditoria router — query audit log with filters.

All endpoints require auditoria:ver permission.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/auditoria", dependencies=[Depends(require_permission("auditoria:ver"))])
async def listar_auditoria(
    accion: str | None = Query(None),
    materia_id: str | None = Query(None),
    actor_id: str | None = Query(None),
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List audit log entries for the current tenant with optional filters."""
    audit = AuditLogService(session)
    filtros = {
        k: v
        for k, v in {
            "accion": accion,
            "materia_id": materia_id,
            "actor_id": actor_id,
            "desde": desde,
            "hasta": hasta,
        }.items()
        if v is not None
    }
    logs = await audit.get_all(current_user.tenant_id, filtros, limit)
    return [
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "accion": l.accion,
            "materia_id": l.materia_id,
            "detalle": l.detalle,
            "filas_afectadas": l.filas_afectadas,
            "ip": l.ip,
            "user_agent": l.user_agent,
            "impersonado_id": l.impersonado_id,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
