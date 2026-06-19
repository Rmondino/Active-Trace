"""SlotEncuentroRepository — CRUD for SlotEncuentro with tenant scope."""

from sqlalchemy import select

from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    model_class = SlotEncuentro

    async def get_by_materia(self, materia_id: str) -> list[SlotEncuentro]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.order_by(self.model_class.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
