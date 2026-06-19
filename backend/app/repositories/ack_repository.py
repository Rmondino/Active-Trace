"""AckRepository — queries for AcknowledgmentAviso model."""

from sqlalchemy import func, select

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.repositories.base import BaseRepository


class AckRepository(BaseRepository[AcknowledgmentAviso]):
    """Repository for AcknowledgmentAviso entity."""

    model_class = AcknowledgmentAviso

    async def has_ack(self, aviso_id: str, usuario_id: str) -> bool:
        """Check if a user has already acknowledged a notice.

        Args:
            aviso_id: The notice UUID.
            usuario_id: The user UUID.

        Returns:
            True if the user has acknowledged this notice.
        """
        stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(
                AcknowledgmentAviso.tenant_id == self.tenant_id,
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.usuario_id == usuario_id,
                AcknowledgmentAviso.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count_by_aviso(self, aviso_id: str) -> int:
        """Count total acknowledgments for a notice.

        Args:
            aviso_id: The notice UUID.

        Returns:
            Total number of acknowledgments.
        """
        stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(
                AcknowledgmentAviso.tenant_id == self.tenant_id,
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar()
