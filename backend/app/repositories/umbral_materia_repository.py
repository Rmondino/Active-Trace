"""UmbralMateriaRepository — CRUD for UmbralMateria with tenant scope."""

from sqlalchemy import select

from app.models.umbral_materia import UmbralMateria
from app.repositories.base import BaseRepository


class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    model_class = UmbralMateria

    async def get_by_asignacion_materia(
        self, asignacion_id: str, materia_id: str
    ) -> UmbralMateria | None:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.asignacion_id == asignacion_id,
            self.model_class.materia_id == materia_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, umbral: UmbralMateria) -> UmbralMateria:
        existing = await self.get_by_asignacion_materia(
            umbral.asignacion_id, umbral.materia_id
        )
        if existing:
            existing.umbral_pct = umbral.umbral_pct
            existing.valores_aprobatorios = umbral.valores_aprobatorios
            await self.session.flush()
            return existing
        self.session.add(umbral)
        await self.session.flush()
        return umbral

    async def get_by_materia(self, materia_id: str) -> UmbralMateria | None:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self) -> int:
        return 60

    @staticmethod
    def get_default_valores_aprobatorios() -> list[str]:
        return ["Satisfactorio", "Supera lo esperado"]
