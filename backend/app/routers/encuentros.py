"""Encuentros router — slots, instancias, contenido aula, vista admin."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.services.encuentro_service import EncuentroService

router = APIRouter(prefix="/api/encuentros", tags=["encuentros"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _build_svc(
    db: AsyncSession, tenant_id: str
) -> EncuentroService:
    slot_repo = SlotEncuentroRepository(session=db, tenant_id=tenant_id)
    instancia_repo = InstanciaEncuentroRepository(session=db, tenant_id=tenant_id)
    return EncuentroService(db, slot_repo, instancia_repo, tenant_id)


@router.post("/slots", status_code=201)
async def crear_slot(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    result = await svc.crear_slot(body, current_user.id)
    return {
        "slot": {
            "id": result["slot"].id,
            "titulo": result["slot"].titulo,
            "hora": result["slot"].hora,
            "materia_id": result["slot"].materia_id,
        },
        "instancias": [
            {
                "id": i.id,
                "fecha": i.fecha.isoformat(),
                "hora": i.hora,
                "titulo": i.titulo,
                "estado": i.estado,
            }
            for i in result["instancias"]
        ],
    }


@router.get("/slots")
async def listar_slots(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    slots = await svc.listar_slots(materia_id)
    return {"slots": [
        {
            "id": s.id,
            "titulo": s.titulo,
            "hora": s.hora,
            "materia_id": s.materia_id,
            "dia_semana": s.dia_semana,
            "fecha_inicio": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
            "cant_semanas": s.cant_semanas,
            "fecha_unica": s.fecha_unica.isoformat() if s.fecha_unica else None,
            "vig_desde": s.vig_desde.isoformat(),
            "vig_hasta": s.vig_hasta.isoformat(),
        }
        for s in slots
    ]}


@router.get("/slots/{id}")
async def detalle_slot(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    result = await svc.get_slot_detalle(id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Slot no encontrado")
    return result


@router.patch("/instancias/{id}")
async def editar_instancia(
    id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    instancia = await svc.editar_instancia(id, body)
    return {
        "id": instancia.id,
        "estado": instancia.estado,
        "meet_url": instancia.meet_url,
        "video_url": instancia.video_url,
        "comentario": instancia.comentario,
    }


@router.get("/instancias")
async def listar_instancias(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    instancias = await svc.listar_instancias(materia_id)
    return {"instancias": [
        {
            "id": i.id,
            "slot_id": i.slot_id,
            "fecha": i.fecha.isoformat(),
            "hora": i.hora,
            "titulo": i.titulo,
            "estado": i.estado,
            "meet_url": i.meet_url,
            "video_url": i.video_url,
            "comentario": i.comentario,
        }
        for i in instancias
    ]}


@router.get("/contenido-aula")
async def contenido_aula(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    html = await svc.generar_contenido_aula(materia_id)
    return Response(content=html, media_type="text/html")


@router.get("/vista-admin")
async def vista_admin(
    materia_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    filtros = {}
    if materia_id:
        filtros["materia_id"] = materia_id
    data = await svc.vista_admin(filtros)
    return {"encuentros": data}
