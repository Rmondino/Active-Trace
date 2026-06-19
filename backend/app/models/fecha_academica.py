"""FechaAcademica model — academic calendar dates per tenant.

Represents a scheduled academic event (exam, assignment, colloquium, retake)
for a subject and cohort within a period.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class FechaAcademica(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """An academic calendar date for a subject and cohort.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        materia_id: FK to the subject.
        cohorte_id: FK to the cohort.
        tipo: Type of event — "Parcial", "TP", "Coloquio", "Recuperatorio".
        numero: Sequential number (1st partial, 2nd partial, etc.).
        periodo: Academic period string (e.g. "2026-1").
        fecha: Date of the event.
        titulo: Title/description of the event.
    """

    __tablename__ = "fecha_academica"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "materia_id", "cohorte_id", "tipo", "numero", "periodo",
            name="uq_fecha_academica",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    materia_id: Mapped[str] = mapped_column(
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[str] = mapped_column(
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    numero: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    periodo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FechaAcademica(id={self.id}, tipo={self.tipo}, numero={self.numero})>"
