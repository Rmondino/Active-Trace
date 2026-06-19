"""FechaAcademicaRepository — CRUD for FechaAcademica model with tenant scope."""

from typing import Any

from sqlalchemy import select, func

from app.models.fecha_academica import FechaAcademica
from app.repositories.base import BaseRepository


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    """Repository for FechaAcademica entity with tenant-scoped queries."""

    model_class = FechaAcademica

    async def exists_by_unique(
        self, materia_id: str, cohorte_id: str, tipo: str, numero: int, periodo: str,
    ) -> bool:
        """Check if a date exists for the given unique combination.

        Args:
            materia_id: The subject UUID.
            cohorte_id: The cohort UUID.
            tipo: Event type.
            numero: Event number.
            periodo: Academic period.

        Returns:
            True if a record exists for this combination.
        """
        stmt = select(func.count()).select_from(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.where(self.model_class.cohorte_id == cohorte_id)
        stmt = stmt.where(self.model_class.tipo == tipo)
        stmt = stmt.where(self.model_class.numero == numero)
        stmt = stmt.where(self.model_class.periodo == periodo)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def list_by_filters(self, **filters: Any) -> list[FechaAcademica]:
        """List dates filtered by optional criteria.

        Supported filters: materia_id, cohorte_id, tipo, periodo.
        All filters are AND-ed together. Only provided filters are applied.

        Returns:
            List of matching FechaAcademica instances.
        """
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)

        for column_name, value in filters.items():
            if value is not None:
                column = getattr(self.model_class, column_name, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
