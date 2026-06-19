"""ReservaRepository — CRUD for ReservaEvaluacion with tenant scope."""

from datetime import date

from sqlalchemy import func, select

from app.models.reserva_evaluacion import ReservaEvaluacion
from app.repositories.base import BaseRepository


class ReservaRepository(BaseRepository[ReservaEvaluacion]):
    model_class = ReservaEvaluacion

    async def get_by_evaluacion(self, evaluacion_id: str) -> list[ReservaEvaluacion]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.evaluacion_id == evaluacion_id)
        stmt = stmt.order_by(self.model_class.fecha, self.model_class.hora)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_alumno_evaluacion(
        self, alumno_id: str, evaluacion_id: str,
    ) -> ReservaEvaluacion | None:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.alumno_id == alumno_id,
            self.model_class.evaluacion_id == evaluacion_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_activas_by_fecha(
        self, evaluacion_id: str, fecha: date,
    ) -> int:
        stmt = select(func.count(self.model_class.id))
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.evaluacion_id == evaluacion_id,
            self.model_class.fecha == fecha,
            self.model_class.estado == "Activa",
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
