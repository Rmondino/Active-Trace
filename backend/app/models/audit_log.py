"""AuditLog model — append-only audit trail for all domain actions.

Every action that modifies domain state must create an AuditLog entry.
This table is APPEND-ONLY: never UPDATE or DELETE rows.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.id"),
        nullable=False,
        index=True,
    )
    accion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        index=True,
    )
    detalle: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    ip: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, accion={self.accion})>"
