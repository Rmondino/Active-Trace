"""CarreraRepository — CRUD for Carrera model with tenant scope."""

from sqlalchemy import select, func

from app.models.carrera import Carrera
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    """Repository for Carrera entity with tenant-scoped queries."""

    model_class = Carrera

    async def exists_by_codigo(self, codigo: str) -> bool:
        """Check if a carrera with the given codigo exists in this tenant.

        Args:
            codigo: The career code to check.

        Returns:
            True if a carrera with this codigo exists (active, not soft-deleted).
        """
        stmt = select(func.count()).select_from(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.codigo == codigo)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0
