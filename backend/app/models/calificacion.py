import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Calificacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "calificacion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    entrada_padron_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("entrada_padron.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actividad: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    nota_numerica: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    nota_textual: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    origen: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    entrada_padron = relationship("EntradaPadron", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "entrada_padron_id", "actividad",
            name="uq_calificacion_entrada_actividad",
        ),
        Index("ix_calificacion_tenant_materia", "tenant_id", "materia_id"),
    )

    def __repr__(self) -> str:
        return f"<Calificacion(id={self.id}, actividad={self.actividad}, aprobado={self.aprobado})>"
