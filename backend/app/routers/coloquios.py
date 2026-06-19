"""Coloquios router — evaluaciones, reservas y resultados."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.asignacion import Asignacion
from app.models.user import User
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.resultado_repository import ResultadoRepository
from app.schemas.coloquios import (
    AdminGlobalItem,
    AlumnosImport,
    EvaluacionCreate,
    EvaluacionDetalle,
    EvaluacionRead,
    ReservaCreate,
    ReservaRead,
    ResultadoCreate,
    ResultadoRead,
)
from app.services.coloquio_service import ColoquioService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/api/coloquios", tags=["coloquios"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _build_svc(db: AsyncSession, tenant_id: str) -> ColoquioService:
    ev_repo = EvaluacionRepository(session=db, tenant_id=tenant_id)
    res_repo = ReservaRepository(session=db, tenant_id=tenant_id)
    rt_repo = ResultadoRepository(session=db, tenant_id=tenant_id)
    return ColoquioService(db, ev_repo, res_repo, rt_repo, tenant_id)


async def _get_user_roles(db: AsyncSession, user: User) -> list[str]:
    result = await db.execute(
        select(Asignacion.rol).where(
            Asignacion.usuario_id == user.id,
            Asignacion.tenant_id == user.tenant_id,
            Asignacion.deleted_at.is_(None),
        )
    )
    return list(set(row[0] for row in result.all()))


@router.post("", status_code=201, response_model=EvaluacionRead)
async def crear(
    body: EvaluacionCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    evaluacion = await svc.crear(body.model_dump(), current_user.id)
    return EvaluacionRead(
        id=evaluacion.id,
        materia_id=evaluacion.materia_id,
        cohorte_id=evaluacion.cohorte_id,
        tipo=evaluacion.tipo,
        instancia=evaluacion.instancia,
        dias_disponibles=evaluacion.dias_disponibles,
        cupo_por_dia=evaluacion.cupo_por_dia,
        activa=evaluacion.activa,
        convocados=evaluacion.convocados or [],
    )


@router.get("", response_model=list[EvaluacionRead])
async def listar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    ps = PermissionService(db)
    has_gestionar = await ps.has_permission(current_user, "coloquios:gestionar")
    if has_gestionar:
        evaluaciones = await svc.listar()
    else:
        roles = await _get_user_roles(db, current_user)
        evaluaciones = await svc.listar(
            usuario_id=current_user.id,
            roles=roles,
        )
    return [EvaluacionRead(**e) for e in evaluaciones]


@router.get("/admin")
async def admin_global(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    return {"evaluaciones": await svc.admin_global()}


@router.get("/{id}", response_model=EvaluacionDetalle)
async def detalle(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    return await svc.detalle(id)


@router.post("/{id}/alumnos")
async def importar_alumnos(
    id: str,
    body: AlumnosImport,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    return await svc.importar_alumnos(id, body.alumno_ids)


@router.post("/{id}/reservar", status_code=201, response_model=ReservaRead)
async def reservar(
    id: str,
    body: ReservaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    reserva = await svc.reservar(id, current_user.id, body.fecha, body.hora)
    return ReservaRead(
        id=reserva.id,
        evaluacion_id=reserva.evaluacion_id,
        alumno_id=reserva.alumno_id,
        fecha=reserva.fecha,
        hora=reserva.hora,
        estado=reserva.estado,
    )


@router.get("/{id}/reservas", response_model=list[ReservaRead])
async def listar_reservas(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    reservas = await svc.listar_reservas(id)
    return [
        ReservaRead(
            id=r.id,
            evaluacion_id=r.evaluacion_id,
            alumno_id=r.alumno_id,
            fecha=r.fecha,
            hora=r.hora,
            estado=r.estado,
        )
        for r in reservas
    ]


@router.patch("/reservas/{id}")
async def cancelar_reserva(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    await svc.cancelar_reserva(id, current_user.id)
    return {"detail": "Reserva cancelada"}


@router.post("/{id}/resultados", status_code=201, response_model=ResultadoRead)
async def registrar_resultado(
    id: str,
    body: ResultadoCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    resultado = await svc.registrar_resultado(id, body.alumno_id, body.nota_final)
    return ResultadoRead(
        id=resultado.id,
        evaluacion_id=resultado.evaluacion_id,
        alumno_id=resultado.alumno_id,
        nota_final=resultado.nota_final,
    )


@router.get("/{id}/resultados", response_model=list[ResultadoRead])
async def ver_resultados(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("coloquios:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    resultados = await svc.listar_resultados(id)
    return [
        ResultadoRead(
            id=r.id,
            evaluacion_id=r.evaluacion_id,
            alumno_id=r.alumno_id,
            nota_final=r.nota_final,
        )
        for r in resultados
    ]
