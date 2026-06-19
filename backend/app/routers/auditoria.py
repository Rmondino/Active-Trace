"""Auditoria metrics router — dashboard endpoints for usage analytics.

All endpoints require auditoria:ver permission.
ADMIN sees all data; COORDINADOR sees only their own actions (scope propio).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.services.auditoria_metrics_service import AuditoriaMetricsService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])


@router.get(
    "/acciones-por-dia",
    dependencies=[Depends(require_permission(
        "auditoria:ver",
        owner_check=lambda _req, _user: True,
    ))],
)
async def acciones_por_dia(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    actor_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ps = PermissionService(session)
    scope = await ps.get_permission_scope(current_user, "auditoria:ver")
    if scope == "propio":
        actor_id = current_user.id
    svc = AuditoriaMetricsService(session)
    return await svc.acciones_por_dia(
        tenant_id=current_user.tenant_id,
        desde=desde,
        hasta=hasta,
        actor_id=actor_id,
    )


@router.get(
    "/comunicaciones-por-docente",
    dependencies=[Depends(require_permission(
        "auditoria:ver",
        owner_check=lambda _req, _user: True,
    ))],
)
async def comunicaciones_por_docente(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    svc = AuditoriaMetricsService(session)
    return await svc.comunicaciones_por_docente(tenant_id=current_user.tenant_id)


@router.get(
    "/interacciones-por-docente-materia",
    dependencies=[Depends(require_permission(
        "auditoria:ver",
        owner_check=lambda _req, _user: True,
    ))],
)
async def interacciones_por_docente_materia(
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    actor_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ps = PermissionService(session)
    scope = await ps.get_permission_scope(current_user, "auditoria:ver")
    if scope == "propio":
        actor_id = current_user.id
    svc = AuditoriaMetricsService(session)
    return await svc.interacciones_por_docente_materia(
        tenant_id=current_user.tenant_id,
        desde=desde,
        hasta=hasta,
        actor_id=actor_id,
    )


@router.get(
    "/ultimas-acciones",
    dependencies=[Depends(require_permission(
        "auditoria:ver",
        owner_check=lambda _req, _user: True,
    ))],
)
async def ultimas_acciones(
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ps = PermissionService(session)
    scope = await ps.get_permission_scope(current_user, "auditoria:ver")
    actor_id: str | None = None
    if scope == "propio":
        actor_id = current_user.id
    svc = AuditoriaMetricsService(session)
    return await svc.ultimas_acciones(
        tenant_id=current_user.tenant_id,
        limit=limit,
        actor_id=actor_id,
    )


@router.get(
    "/log",
    dependencies=[Depends(require_permission(
        "auditoria:ver",
        owner_check=lambda _req, _user: True,
    ))],
)
async def log_completo(
    accion: str | None = Query(None),
    materia_id: str | None = Query(None),
    actor_id: str | None = Query(None),
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ps = PermissionService(session)
    scope = await ps.get_permission_scope(current_user, "auditoria:ver")
    resolved_actor = actor_id
    if scope == "propio":
        resolved_actor = current_user.id
    filtros = {
        k: v
        for k, v in {
            "accion": accion,
            "materia_id": materia_id,
            "actor_id": resolved_actor,
            "desde": desde,
            "hasta": hasta,
        }.items()
        if v is not None
    }
    svc = AuditoriaMetricsService(session)
    return await svc.log_completo(
        tenant_id=current_user.tenant_id,
        filtros=filtros,
        limit=limit,
    )
