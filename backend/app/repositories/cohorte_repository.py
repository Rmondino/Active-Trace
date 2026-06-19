"""CohorteRepository — CRUD for Cohorte model with tenant scope and business rules."""

from sqlalchemy import select, func

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.repositories.base import BaseRepository


class CohorteRepository(BaseRepository[Cohorte]):
    """Repository for Cohorte entity with tenant-scoped queries and business validation."""

    model_class = Cohorte

    async def exists_by_nombre_y_carrera(self, nombre: str, carrera_id: str) -> bool:
        """Check if a cohorte with the given nombre exists for a carrera in this tenant.

        Args:
            nombre: The cohort name to check.
            carrera_id: The carrera UUID.

        Returns:
            True if a cohorte exists with this nombre and carrera_id.
        """
        stmt = select(func.count()).select_from(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.nombre == nombre)
        stmt = stmt.where(self.model_class.carrera_id == carrera_id)
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def create(self, data: dict) -> Cohorte:
        """Create a cohorte with business rule: carrera inactiva no admite cohortes abiertas.

        Args:
            data: Dictionary of column values.

        Returns:
            The created Cohorte instance.

        Raises:
            ValueError: If the carrera is inactive and vig_hasta is not set (open cohort).
        """
        carrera_id = data.get("carrera_id")
        vig_hasta = data.get("vig_hasta")

        # Check business rule: inactive carrera cannot have open cohorts
        if carrera_id and not vig_hasta:
            stmt = select(Carrera.estado).where(Carrera.id == carrera_id)
            result = await self.session.execute(stmt)
            carrera_estado = result.scalar_one_or_none()
            if carrera_estado == "Inactiva":
                raise ValueError(
                    "No se pueden crear cohortes abiertas para una carrera inactiva"
                )

        return await super().create(data)
