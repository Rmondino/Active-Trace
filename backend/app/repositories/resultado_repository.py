"""ResultadoRepository — CRUD for ResultadoEvaluacion with tenant scope."""

from sqlalchemy import select

from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.repositories.base import BaseRepository


class ResultadoRepository(BaseRepository[ResultadoEvaluacion]):
    model_class = ResultadoEvaluacion

    async def get_by_evaluacion(self, evaluacion_id: str) -> list[ResultadoEvaluacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.evaluacion_id == evaluacion_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_alumno_evaluacion(
        self, alumno_id: str, evaluacion_id: str,
    ) -> ResultadoEvaluacion | None:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.alumno_id == alumno_id,
            self.model_class.evaluacion_id == evaluacion_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
