"""CalificacionRepository — CRUD for Calificacion with tenant scope."""

from datetime import UTC, datetime

from sqlalchemy import select, update

from app.models.calificacion import Calificacion
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    model_class = Calificacion

    async def get_by_materia(self, materia_id: str) -> list[Calificacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_entrada(self, entrada_padron_id: str) -> list[Calificacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.entrada_padron_id == entrada_padron_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_actividades_by_materia(self, materia_id: str) -> list[str]:
        stmt = select(self.model_class.actividad).distinct()
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, calificaciones: list[Calificacion]) -> None:
        self.session.add_all(calificaciones)
        await self.session.flush()

    async def vaciar_materia(self, materia_id: str) -> None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.materia_id == materia_id)
            .values(deleted_at=datetime.now(UTC))
        )
        stmt = self._apply_tenant_scope(stmt)
        await self.session.execute(stmt)
        await self.session.flush()
