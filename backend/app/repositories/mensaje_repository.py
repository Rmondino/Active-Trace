"""MensajeRepository — queries for Mensaje model with tenant scope."""

from datetime import UTC, datetime

from sqlalchemy import func, select, update

from app.models.mensaje import Mensaje
from app.repositories.base import BaseRepository


class MensajeRepository(BaseRepository[Mensaje]):
    model_class = Mensaje

    async def listar_recibidos(self, tenant_id: str, usuario_id: str) -> list[Mensaje]:
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.destinatario_id == usuario_id,
                Mensaje.deleted_at.is_(None),
            )
            .order_by(Mensaje.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def listar_enviados(self, tenant_id: str, usuario_id: str) -> list[Mensaje]:
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.remitente_id == usuario_id,
                Mensaje.deleted_at.is_(None),
            )
            .order_by(Mensaje.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def marcar_leido(self, mensaje_id: str) -> None:
        stmt = (
            update(Mensaje)
            .where(Mensaje.id == mensaje_id)
            .values(leido=True, leido_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def contar_no_leidos(self, tenant_id: str, usuario_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Mensaje)
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.destinatario_id == usuario_id,
                Mensaje.leido.is_(False),
                Mensaje.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
