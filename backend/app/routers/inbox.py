"""Inbox router — mensajería interna entre usuarios.

Endpoints:
    - GET  /api/inbox — listar mensajes recibidos
    - GET  /api/inbox/no-leidos — count de no leídos
    - GET  /api/inbox/enviados — mensajes enviados
    - GET  /api/inbox/{id} — detalle (marca leído)
    - POST /api/inbox — enviar nuevo mensaje
    - POST /api/inbox/{id}/responder — responder
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.repositories.mensaje_repository import MensajeRepository
from app.schemas.mensaje import MensajeCreate, MensajeResponder
from app.services.mensaje_service import MensajeService

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


def _build_svc(db: AsyncSession, tenant_id: str) -> MensajeService:
    repo = MensajeRepository(session=db, tenant_id=tenant_id)
    return MensajeService(repo=repo, session=db)


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.get("")
async def listar_recibidos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    mensajes = await svc.listar_recibidos(tenant_id, current_user.id)
    return [svc._to_dict(m) for m in mensajes]


@router.get("/enviados")
async def listar_enviados(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    mensajes = await svc.listar_enviados(tenant_id, current_user.id)
    return [svc._to_dict(m) for m in mensajes]


@router.get("/no-leidos")
async def contar_no_leidos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    count = await svc.contar_no_leidos(tenant_id, current_user.id)
    return {"count": count}


@router.get("/{id}")
async def detalle(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    mensaje = await svc.obtener_mensaje(tenant_id, id, current_user.id)
    if mensaje is None:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return svc._to_dict(mensaje)


@router.post("", status_code=201)
async def enviar(
    body: MensajeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    mensaje = await svc.enviar_mensaje(
        tenant_id=tenant_id,
        remitente_id=current_user.id,
        destinatario_id=body.destinatario_id,
        asunto=body.asunto,
        cuerpo=body.cuerpo,
    )
    return svc._to_dict(mensaje)


@router.post("/{id}/responder", status_code=201)
async def responder(
    id: str,
    body: MensajeResponder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    mensaje = await svc.responder_mensaje(
        tenant_id=tenant_id,
        usuario_id=current_user.id,
        mensaje_padre_id=id,
        cuerpo=body.cuerpo,
    )
    if mensaje is None:
        raise HTTPException(status_code=404, detail="Mensaje original no encontrado")
    return svc._to_dict(mensaje)
