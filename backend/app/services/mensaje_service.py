"""MensajeService — internal messaging between users."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje import Mensaje
from app.repositories.mensaje_repository import MensajeRepository

logger = logging.getLogger(__name__)


class MensajeService:

    def __init__(self, repo: MensajeRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def enviar_mensaje(
        self,
        tenant_id: str,
        remitente_id: str,
        destinatario_id: str,
        asunto: str,
        cuerpo: str,
        mensaje_padre_id: str | None = None,
    ) -> Mensaje:
        mensaje = Mensaje(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            remitente_id=remitente_id,
            destinatario_id=destinatario_id,
            asunto=asunto,
            cuerpo=cuerpo,
            mensaje_padre_id=mensaje_padre_id,
        )
        self.session.add(mensaje)
        await self.session.flush()
        return mensaje

    async def listar_recibidos(self, tenant_id: str, usuario_id: str) -> list[Mensaje]:
        return await self.repo.listar_recibidos(tenant_id, usuario_id)

    async def listar_enviados(self, tenant_id: str, usuario_id: str) -> list[Mensaje]:
        return await self.repo.listar_enviados(tenant_id, usuario_id)

    async def obtener_mensaje(
        self, tenant_id: str, mensaje_id: str, usuario_id: str
    ) -> Mensaje | None:
        mensaje = await self.repo.get(mensaje_id)
        if mensaje is None:
            return None
        if mensaje.destinatario_id == usuario_id and not mensaje.leido:
            mensaje.leido = True
            mensaje.leido_at = datetime.now(UTC)
            await self.session.flush()
        return mensaje

    async def responder_mensaje(
        self,
        tenant_id: str,
        usuario_id: str,
        mensaje_padre_id: str,
        cuerpo: str,
    ) -> Mensaje | None:
        padre = await self.repo.get(mensaje_padre_id)
        if padre is None:
            return None
        return await self.enviar_mensaje(
            tenant_id=tenant_id,
            remitente_id=usuario_id,
            destinatario_id=padre.remitente_id,
            asunto=f"Re: {padre.asunto}",
            cuerpo=cuerpo,
            mensaje_padre_id=mensaje_padre_id,
        )

    async def contar_no_leidos(self, tenant_id: str, usuario_id: str) -> int:
        return await self.repo.contar_no_leidos(tenant_id, usuario_id)

    def _to_dict(self, m: Mensaje) -> dict:
        return {
            "id": m.id,
            "tenant_id": m.tenant_id,
            "remitente_id": m.remitente_id,
            "destinatario_id": m.destinatario_id,
            "asunto": m.asunto,
            "cuerpo": m.cuerpo,
            "leido": m.leido,
            "leido_at": m.leido_at.isoformat() if m.leido_at else None,
            "mensaje_padre_id": m.mensaje_padre_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
