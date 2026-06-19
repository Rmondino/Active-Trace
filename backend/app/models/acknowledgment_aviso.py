"""AcknowledgmentAviso model — records user acknowledgment of a notice."""

import uuid

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class AcknowledgmentAviso(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """Records that a user acknowledged a specific notice.

    Enforces unique (tenant_id, aviso_id, usuario_id) — one ack per user per aviso.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        aviso_id: FK to the acknowledged notice.
        usuario_id: FK to the acknowledging user.
        confirmado_at: Timestamp of acknowledgment.
    """

    __tablename__ = "acknowledgment_aviso"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "aviso_id", "usuario_id",
            name="uq_ack_aviso_tenant_aviso_usuario",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    aviso_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("aviso.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AcknowledgmentAviso(aviso_id={self.aviso_id}, usuario_id={self.usuario_id})>"
