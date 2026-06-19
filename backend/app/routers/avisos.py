"""Avisos router — notice board CRUD, visibility, acknowledgment, and stats."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.ack_repository import AckRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.aviso import AcknowledgmentRead, AvisoCreate, AvisoRead, AvisoStats, AvisoUpdate
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/avisos", tags=["avisos"])


def _build_svc(db: AsyncSession, tenant_id: str) -> AvisoService:
    aviso_repo = AvisoRepository(session=db, tenant_id=tenant_id)
    ack_repo = AckRepository(session=db, tenant_id=tenant_id)
    return AvisoService(aviso_repo=aviso_repo, ack_repo=ack_repo, session=db)


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.post("", status_code=201, dependencies=[Depends(require_permission("avisos:publicar"))])
async def crear(
    body: AvisoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    aviso = await svc.crear(body.model_dump(), tenant_id)
    return svc._to_dict(aviso)


@router.get("")
async def listar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    """List visible notices for the authenticated user (scoped by role and asignaciones)."""
    asignacion_repo = AsignacionRepository(session=db, tenant_id=tenant_id)
    roles = await asignacion_repo.get_active_role_slugs(tenant_id, current_user.id)
    asignaciones = await asignacion_repo.get_by_usuario(
        tenant_id, current_user.id, solo_vigentes=True,
    )
    svc = _build_svc(db, tenant_id)
    return await svc.listar_visibles(
        current_user.id, tenant_id, roles, asignaciones,
    )


@router.get("/{id}")
async def detalle(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    aviso = await svc.aviso_repo.get(id)
    if aviso is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    ackeado = await svc.ack_repo.has_ack(aviso.id, current_user.id)
    return svc._to_dict(aviso, ackeado=ackeado)


@router.put("/{id}", dependencies=[Depends(require_permission("avisos:publicar"))])
async def actualizar(
    id: str,
    body: AvisoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    # Filter out None values so we only update provided fields
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    aviso = await svc.actualizar(id, data, tenant_id)
    if aviso is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    ackeado = await svc.ack_repo.has_ack(aviso.id, current_user.id)
    return svc._to_dict(aviso, ackeado=ackeado)


@router.delete("/{id}", status_code=204, dependencies=[Depends(require_permission("avisos:publicar"))])
async def eliminar(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    deleted = await svc.aviso_repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")


@router.post("/{id}/ack", status_code=201)
async def ack(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        result = await svc.ack(id, current_user.id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return AcknowledgmentRead(
        id=result.id,
        aviso_id=result.aviso_id,
        usuario_id=result.usuario_id,
        confirmado_at=result.confirmado_at,
    )


@router.get("/{id}/stats", dependencies=[Depends(require_permission("avisos:publicar"))])
async def stats(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    return await svc.stats(id, tenant_id)
