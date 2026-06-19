"""ComunicacionRepository — CRUD for Comunicacion with state machine support."""

from sqlalchemy import select, func, or_, text

from app.models.comunicacion import Comunicacion
from app.repositories.base import BaseRepository


class ComunicacionRepository(BaseRepository[Comunicacion]):
    model_class = Comunicacion

    async def bulk_create(self, comunicaciones: list[Comunicacion]) -> None:
        for c in comunicaciones:
            if hasattr(c, "tenant_id"):
                c.tenant_id = self.tenant_id
            self.session.add(c)
        await self.session.flush()

    async def get_by_lote(self, lote_id: str) -> list[Comunicacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.lote_id == lote_id)
        stmt = stmt.order_by(self.model_class.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_materia(self, materia_id: str) -> list[Comunicacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.order_by(self.model_class.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pendientes_aprobacion(self) -> list[Comunicacion]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.estado == "Pendiente",
                self.model_class.aprobado_por.is_(None),
            )
        )
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.order_by(self.model_class.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pendientes_envio(
        self, limit: int = 20
    ) -> list[Comunicacion]:
        subq = (
            select(func.count(text("1")))
            .select_from(text("tenant"))
            .where(
                text("tenant.id = comunicacion.tenant_id"),
                text(
                    "COALESCE((tenant.config->>'aprobacion_requerida')::boolean, false) = true"
                ),
            )
        )
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.estado == "Pendiente",
                or_(
                    self.model_class.aprobado_por.isnot(None),
                    ~subq.exists(),
                ),
            )
        )
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.order_by(self.model_class.created_at.asc())
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def actualizar_estado(
        self, id: str, estado: str, **kwargs
    ) -> Comunicacion | None:
        record = await self.get(id)
        if record is None:
            return None
        record.estado = estado
        for key, value in kwargs.items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def count_by_lote(self, lote_id: str) -> dict[str, int]:
        stmt = (
            select(
                self.model_class.estado,
                func.count(self.model_class.id),
            )
            .where(
                self.model_class.lote_id == lote_id,
            )
            .group_by(self.model_class.estado)
        )
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
