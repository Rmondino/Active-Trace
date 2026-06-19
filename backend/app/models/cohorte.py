"""Cohorte model — cohort/group within an academic career.

Represents a specific cohort (e.g. "MAR-2026 intake") tied to a career.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Cohorte(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A cohort within a career.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        carrera_id: FK to the parent career.
        nombre: Cohort name unique per (tenant, carrera) (e.g. "MAR-2026").
        anio: Academic year.
        vig_desde: Start date of validity.
        vig_hasta: End date of validity (null = open cohort).
        estado: "Activa" or "Inactiva".
    """

    __tablename__ = "cohorte"
    __table_args__ = (
        UniqueConstraint("tenant_id", "carrera_id", "nombre", name="uq_cohorte_tenant_carrera_nombre"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    carrera_id: Mapped[str] = mapped_column(
        ForeignKey("carrera.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    anio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    vig_desde: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    vig_hasta: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        default=None,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Activa",
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Cohorte(id={self.id}, nombre={self.nombre})>"
