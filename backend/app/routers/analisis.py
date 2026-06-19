"""Analisis router — endpoints for academic analysis and monitoring.

All endpoints require `atrasados:ver` permission.
Scope `general` in monitor requires COORDINADOR or ADMIN role.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.repositories.version_padron_repository import VersionPadronRepository
from app.services.analisis_service import AnalisisService

router = APIRouter(prefix="/api/analisis", tags=["analisis"])


def _get_analisis_service(db: AsyncSession, tenant_id: str) -> AnalisisService:
    return AnalisisService(
        calificacion_repo=CalificacionRepository(session=db, tenant_id=tenant_id),
        umbral_repo=UmbralMateriaRepository(session=db, tenant_id=tenant_id),
        version_padron_repo=VersionPadronRepository(session=db, tenant_id=tenant_id),
        entrada_padron_repo=EntradaPadronRepository(session=db, tenant_id=tenant_id),
        asignacion_repo=AsignacionRepository(session=db, tenant_id=tenant_id),
    )


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.get("/atrasados")
async def get_atrasados(
    materia_id: str = Query(...),
    cohorte_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    service = _get_analisis_service(db, tenant_id)
    result = await service.alumnos_atrasados(materia_id, cohorte_id, tenant_id)
    return result


@router.get("/ranking")
async def get_ranking(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    service = _get_analisis_service(db, tenant_id)
    result = await service.ranking_aprobadas(materia_id, tenant_id)
    return result


@router.get("/reporte-rapido")
async def get_reporte_rapido(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    service = _get_analisis_service(db, tenant_id)
    result = await service.reporte_rapido(materia_id, tenant_id)
    return result


@router.get("/notas-finales")
async def get_notas_finales(
    materia_id: str = Query(...),
    cohorte_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    service = _get_analisis_service(db, tenant_id)
    result = await service.notas_finales(materia_id, cohorte_id, tenant_id)
    return result


@router.get("/exportar-sin-corregir")
async def get_export_sin_corregir(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    service = _get_analisis_service(db, tenant_id)
    xlsx_bytes = await service.exportar_sin_corregir(materia_id, tenant_id)
    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=sin_corregir_{materia_id}.xlsx"
        },
    )


@router.get("/monitor")
async def get_monitor(
    scope: str = Query("propio"),
    materia_id: str | None = Query(None),
    regional: str | None = Query(None),
    comision: str | None = Query(None),
    busqueda: str | None = Query(None),
    actividad: str | None = Query(None),
    estado: str | None = Query(None),
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("atrasados:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    asig_repo = AsignacionRepository(session=db, tenant_id=tenant_id)
    asigs = await asig_repo.get_by_usuario(tenant_id, current_user.id)
    roles = {a.rol.lower() for a in asigs}

    if scope == "general" and "coordinador" not in roles and "admin" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Scope general requiere rol COORDINADOR o ADMIN",
        )

    filtros = {
        "materia_id": materia_id,
        "regional": regional,
        "comision": comision,
        "busqueda": busqueda,
        "actividad": actividad,
        "estado": estado,
        "desde": desde,
        "hasta": hasta,
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}

    service = _get_analisis_service(db, tenant_id)
    result = await service.monitor(scope, filtros, current_user.id, tenant_id)
    return result
