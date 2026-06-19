"""Equipos router — mis equipos, gestión, clonar, exportar."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.asignacion_repository import AsignacionRepository
from app.services.audit_log_service import AuditLogService
from app.services.equipo_service import EquipoService

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _build_svc(
    db: AsyncSession, tenant_id: str
) -> EquipoService:
    repo = AsignacionRepository(session=db, tenant_id=tenant_id)
    audit = AuditLogService(db)
    return EquipoService(repo, audit, db)


@router.get("/mis-equipos")
async def mis_equipos(
    estado: str | None = None,
    materia_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    filtros = {}
    if estado:
        filtros["estado"] = estado
    if materia_id:
        filtros["materia_id"] = materia_id
    result = await svc.mis_equipos(current_user.id, tenant_id, filtros)
    return {"asignaciones": result}


@router.get("/asignaciones")
async def listar_asignaciones(
    materia_id: str | None = None,
    carrera_id: str | None = None,
    cohorte_id: str | None = None,
    usuario_id: str | None = None,
    rol: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    filtros = {}
    if materia_id:
        filtros["materia_id"] = materia_id
    if carrera_id:
        filtros["carrera_id"] = carrera_id
    if cohorte_id:
        filtros["cohorte_id"] = cohorte_id
    if usuario_id:
        filtros["usuario_id"] = usuario_id
    if rol:
        filtros["rol"] = rol
    return await svc.listar_asignaciones(tenant_id, filtros)


@router.post("/asignaciones/masiva", status_code=201)
async def asignacion_masiva(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        return await svc.asignacion_masiva(body, current_user.id, tenant_id)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo requerido: {e}")


@router.post("/clonar", status_code=201)
async def clonar_equipo(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        return await svc.clonar_equipo(body, current_user.id, tenant_id)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo requerido: {e}")


@router.patch("/vigencia")
async def actualizar_vigencia(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        return await svc.actualizar_vigencia(body, current_user.id, tenant_id)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo requerido: {e}")


@router.get("/export")
async def exportar_equipo(
    materia_id: str,
    carrera_id: str,
    cohorte_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    content = await svc.exportar_equipo(materia_id, carrera_id, cohorte_id, tenant_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=equipo_{materia_id}.xlsx"},
    )
