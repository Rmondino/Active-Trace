"""TareaRepository — queries for Tarea model with filtering."""

from sqlalchemy import select

from app.models.tarea import Tarea
from app.repositories.base import BaseRepository


class TareaRepository(BaseRepository[Tarea]):
    """Repository for Tarea entity with tenant-scoped queries."""

    model_class = Tarea

    async def get_by_asignado(
        self,
        tenant_id: str,
        usuario_id: str,
        filtros: dict | None = None,
    ) -> list[Tarea]:
        stmt = (
            select(Tarea)
            .where(
                Tarea.tenant_id == tenant_id,
                Tarea.asignado_a == usuario_id,
                Tarea.deleted_at.is_(None),
            )
        )
        if filtros:
            estado = filtros.get("estado")
            if estado:
                stmt = stmt.where(Tarea.estado == estado)
        stmt = stmt.order_by(Tarea.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_filtered(
        self,
        tenant_id: str,
        filtros: dict | None = None,
    ) -> list[Tarea]:
        stmt = (
            select(Tarea)
            .where(
                Tarea.tenant_id == tenant_id,
                Tarea.deleted_at.is_(None),
            )
        )
        if filtros:
            estado = filtros.get("estado")
            if estado:
                stmt = stmt.where(Tarea.estado == estado)
            materia_id = filtros.get("materia_id")
            if materia_id:
                stmt = stmt.where(Tarea.materia_id == materia_id)
            asignado_a = filtros.get("asignado_a")
            if asignado_a:
                stmt = stmt.where(Tarea.asignado_a == asignado_a)
        stmt = stmt.order_by(Tarea.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
