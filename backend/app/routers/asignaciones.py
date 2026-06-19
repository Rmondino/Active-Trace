"""Asignaciones router — CRUD de asignaciones usuario↔rol↔contexto.

All endpoints require `equipos:asignar` permission (COORDINADOR, ADMIN).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.current_user import get_current_user
from app.models.asignacion import Asignacion
from app.models.user import User

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _compute_estado_vigencia(desde: date, hasta: date | None) -> str:
    """Derive estado_vigencia from dates (not stored)."""
    hoy = date.today()
    if desde <= hoy and (hasta is None or hasta >= hoy):
        return "Vigente"
    return "Vencida"


@router.post("", response_model=dict, status_code=201)
async def create_asignacion(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.asignacion_repository import AsignacionRepository
    from app.schemas.asignacion import AsignacionCreate

    data = AsignacionCreate(**body)
    repo = AsignacionRepository(session=db, tenant_id=tenant_id)

    asig = await repo.create(data.model_dump())

    return {
        "id": asig.id,
        "usuario_id": asig.usuario_id,
        "rol": asig.rol,
        "materia_id": asig.materia_id,
        "carrera_id": asig.carrera_id,
        "cohorte_id": asig.cohorte_id,
        "comisiones": asig.comisiones,
        "responsable_id": asig.responsable_id,
        "desde": str(asig.desde),
        "hasta": str(asig.hasta) if asig.hasta else None,
        "estado_vigencia": _compute_estado_vigencia(asig.desde, asig.hasta),
    }


@router.get("", response_model=list[dict])
async def list_asignaciones(
    usuario_id: str | None = None,
    materia_id: str | None = None,
    rol: str | None = None,
    solo_vigentes: bool = False,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.asignacion_repository import AsignacionRepository

    repo = AsignacionRepository(session=db, tenant_id=tenant_id)

    if usuario_id:
        asignaciones = await repo.get_by_usuario(tenant_id, usuario_id, solo_vigentes=solo_vigentes)
    elif materia_id:
        asignaciones = await repo.get_by_materia(tenant_id, materia_id, solo_vigentes=solo_vigentes)
    elif rol:
        asignaciones = await repo.get_by_rol(tenant_id, rol, solo_vigentes=solo_vigentes)
    else:
        filters = {}
        asignaciones = await repo.list(**filters)

    if solo_vigentes and not any([usuario_id, materia_id, rol]):
        asignaciones = await repo.get_vigentes(tenant_id)

    def _to_response(a: Asignacion) -> dict:
        from app.models.materia import Materia
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte

        materia_nombre = a.materia.nombre if a.materia else ""
        carrera_nombre = a.carrera.nombre if a.carrera else ""
        cohorte_nombre = a.cohorte.nombre if a.cohorte else ""
        return {
            "id": a.id,
            "usuario_id": a.usuario_id,
            "rol": a.rol,
            "materia_id": a.materia_id,
            "materia_nombre": materia_nombre,
            "carrera_id": a.carrera_id,
            "carrera_nombre": carrera_nombre,
            "cohorte_id": a.cohorte_id,
            "cohorte_nombre": cohorte_nombre,
            "comisiones": a.comisiones,
            "responsable_id": a.responsable_id,
            "desde": str(a.desde),
            "hasta": str(a.hasta) if a.hasta else None,
            "estado_vigencia": _compute_estado_vigencia(a.desde, a.hasta),
        }

    return [_to_response(a) for a in asignaciones]


@router.get("/{asignacion_id}", response_model=dict)
async def get_asignacion(
    asignacion_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.asignacion_repository import AsignacionRepository

    repo = AsignacionRepository(session=db, tenant_id=tenant_id)
    asig = await repo.get(asignacion_id)
    if asig is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    return {
        "id": asig.id,
        "usuario_id": asig.usuario_id,
        "rol": asig.rol,
        "materia_id": asig.materia_id,
        "carrera_id": asig.carrera_id,
        "cohorte_id": asig.cohorte_id,
        "comisiones": asig.comisiones,
        "responsable_id": asig.responsable_id,
        "desde": str(asig.desde),
        "hasta": str(asig.hasta) if asig.hasta else None,
        "estado_vigencia": _compute_estado_vigencia(asig.desde, asig.hasta),
    }


@router.put("/{asignacion_id}", response_model=dict)
async def update_asignacion(
    asignacion_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.asignacion_repository import AsignacionRepository
    from app.schemas.asignacion import AsignacionUpdate

    data = AsignacionUpdate(**body)
    repo = AsignacionRepository(session=db, tenant_id=tenant_id)

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    asig = await repo.update(asignacion_id, update_data)
    if asig is None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    return {
        "id": asig.id,
        "usuario_id": asig.usuario_id,
        "rol": asig.rol,
        "materia_id": asig.materia_id,
        "carrera_id": asig.carrera_id,
        "cohorte_id": asig.cohorte_id,
        "comisiones": asig.comisiones,
        "responsable_id": asig.responsable_id,
        "desde": str(asig.desde),
        "hasta": str(asig.hasta) if asig.hasta else None,
        "estado_vigencia": _compute_estado_vigencia(asig.desde, asig.hasta),
    }


@router.delete("/{asignacion_id}", status_code=204)
async def delete_asignacion(
    asignacion_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("equipos:asignar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.asignacion_repository import AsignacionRepository

    repo = AsignacionRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(asignacion_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return None
