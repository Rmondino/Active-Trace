"""AvisoRepository — queries for Aviso model with vigencia filtering."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.models.aviso import Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    """Repository for Aviso entity with tenant-scoped queries."""

    model_class = Aviso

    async def get_activos_vigentes(self, tenant_id: str) -> list[Aviso]:
        """Get active notices within their vigencia window for a tenant.

        Filters: activo=True, deleted_at IS NULL,
                 inicio_en <= now(), fin_en >= now().

        Args:
            tenant_id: The tenant UUID.

        Returns:
            List of vigentes Aviso instances.
        """
        ahora = datetime.now(UTC)
        stmt = (
            select(Aviso)
            .where(
                Aviso.tenant_id == tenant_id,
                Aviso.deleted_at.is_(None),
                Aviso.activo.is_(True),
                Aviso.inicio_en <= ahora,
                Aviso.fin_en >= ahora,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
