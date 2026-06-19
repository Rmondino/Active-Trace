"""Asignacion model — assigns a user to a role within an academic context.

Links a user to a role (PROFESOR, TUTOR, COORDINADOR, etc.) with optional
context (materia, carrera, cohorte) and temporal validity (desde/hasta).

This replaces the deprecated JSONB roles on User.
"""

import uuid

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Asignacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """Assignment of a user to a role within an academic context.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        usuario_id: FK to the assigned user.
        rol: Role name (e.g. "PROFESOR", "TUTOR", "COORDINADOR").
        materia_id: Optional FK to a subject.
        carrera_id: Optional FK to a career.
        cohorte_id: Optional FK to a cohort.
        comisiones: JSONB list of commission names (default []).
        responsable_id: Optional FK to the supervising user.
        desde: Start date of the assignment validity.
        hasta: End date of the assignment validity (None = open-ended).
    """

    __tablename__ = "asignacion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    carrera_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("carrera.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    cohorte_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohorte.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    comisiones: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    responsable_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
    )

    usuario = relationship("User", foreign_keys=[usuario_id], lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
    carrera = relationship("Carrera", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
    responsable = relationship(
        "User", remote_side="User.id", foreign_keys=[responsable_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Asignacion(id={self.id}, rol={self.rol})>"
