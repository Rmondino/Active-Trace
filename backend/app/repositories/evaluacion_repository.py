"""EvaluacionRepository — CRUD for Evaluacion with tenant scope."""

from sqlalchemy import select

from app.models.evaluacion import Evaluacion
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    model_class = Evaluacion

    async def get_activas_by_cohorte(self, cohorte_id: str) -> list[Evaluacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.cohorte_id == cohorte_id,
            self.model_class.activa.is_(True),
        )
        stmt = stmt.order_by(self.model_class.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
