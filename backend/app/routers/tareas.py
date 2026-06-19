"""Tareas router — internal task management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.tarea_repository import TareaRepository
from app.repositories.comentario_repository import ComentarioRepository
from app.schemas.tarea import ComentarioCreate, TareaCreate, TareaRead, TareaUpdateEstado
from app.services.tarea_service import TareaService

router = APIRouter(prefix="/api/tareas", tags=["tareas"])


def _build_svc(db: AsyncSession, tenant_id: str) -> TareaService:
    tarea_repo = TareaRepository(session=db, tenant_id=tenant_id)
    comentario_repo = ComentarioRepository(session=db, tenant_id=tenant_id)
    return TareaService(tarea_repo=tarea_repo, comentario_repo=comentario_repo, session=db)


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _to_tarea_read(tarea: dict) -> TareaRead:
    comentarios = tarea.pop("comentarios", [])
    return TareaRead(**tarea, comentarios=comentarios)


@router.post("", status_code=201, dependencies=[Depends(require_permission("tareas:gestionar"))])
async def crear(
    body: TareaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    tarea = await svc.crear(body.model_dump(), current_user.id, tenant_id)
    return svc._to_dict(tarea)


@router.get("", dependencies=[Depends(require_permission("tareas:gestionar"))])
async def listar_todas(
    estado: str | None = Query(default=None),
    materia_id: str | None = Query(default=None),
    asignado_a: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    filtros = {}
    if estado:
        filtros["estado"] = estado
    if materia_id:
        filtros["materia_id"] = materia_id
    if asignado_a:
        filtros["asignado_a"] = asignado_a
    svc = _build_svc(db, tenant_id)
    return await svc.listar_todas(tenant_id, filtros)


@router.get("/mias")
async def mis_tareas(
    estado: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    return await svc.mis_tareas(current_user.id, tenant_id, estado)


@router.get("/{id}")
async def detalle(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        result = await svc.detalle(id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_tarea_read(result)


@router.patch("/{id}/estado")
async def cambiar_estado(
    id: str,
    body: TareaUpdateEstado,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        tarea = await svc.cambiar_estado(id, body.estado, current_user.id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return svc._to_dict(tarea)


@router.post("/{id}/comentarios", status_code=201)
async def agregar_comentario(
    id: str,
    body: ComentarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        comentario = await svc.agregar_comentario(
            tarea_id=id,
            texto=body.texto,
            autor_id=current_user.id,
            tenant_id=tenant_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": comentario.id,
        "tarea_id": comentario.tarea_id,
        "autor_id": comentario.autor_id,
        "texto": comentario.texto,
        "created_at": comentario.created_at.isoformat() if comentario.created_at else None,
    }
