"""InstanciaEncuentroRepository — CRUD for InstanciaEncuentro with tenant scope."""

from sqlalchemy import select

from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.base import BaseRepository


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    model_class = InstanciaEncuentro

    async def get_by_materia(self, materia_id: str) -> list[InstanciaEncuentro]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.order_by(self.model_class.fecha)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slot(self, slot_id: str) -> list[InstanciaEncuentro]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.slot_id == slot_id)
        stmt = stmt.order_by(self.model_class.fecha)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, instancias: list[InstanciaEncuentro]) -> None:
        self.session.add_all(instancias)
        await self.session.flush()
