"""ProgramaMateriaRepository — CRUD for ProgramaMateria model with tenant scope."""

from sqlalchemy import select, func

from app.models.programa_materia import ProgramaMateria
from app.repositories.base import BaseRepository


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    """Repository for ProgramaMateria entity with tenant-scoped queries."""

    model_class = ProgramaMateria

    async def exists_by_materia_carrera_cohorte(
        self, materia_id: str, carrera_id: str, cohorte_id: str,
    ) -> bool:
        """Check if a program exists for the given materia, carrera and cohorte.

        Args:
            materia_id: The subject UUID.
            carrera_id: The career UUID.
            cohorte_id: The cohort UUID.

        Returns:
            True if a program exists for this combination.
        """
        stmt = select(func.count()).select_from(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.where(self.model_class.carrera_id == carrera_id)
        stmt = stmt.where(self.model_class.cohorte_id == cohorte_id)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0
