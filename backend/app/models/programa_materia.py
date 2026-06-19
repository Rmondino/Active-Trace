"""ProgramaMateria model — subject program/syllabus per tenant.

Represents a program/syllabus document linked to a subject, career, and cohort.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class ProgramaMateria(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A program/syllabus for a subject within a career and cohort.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        materia_id: FK to the subject.
        carrera_id: FK to the career.
        cohorte_id: FK to the cohort.
        titulo: Program title (e.g. "Programa Analítico 2026").
        referencia_archivo: File reference or URL.
        cargado_at: Timestamp when the program was uploaded.
    """

    __tablename__ = "programa_materia"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "materia_id", "carrera_id", "cohorte_id",
            name="uq_programa_materia",
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
    carrera_id: Mapped[str] = mapped_column(
        ForeignKey("carrera.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[str] = mapped_column(
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    referencia_archivo: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProgramaMateria(id={self.id}, titulo={self.titulo})>"
