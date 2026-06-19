"""ReservaEvaluacion model — turno reservado por un alumno para un coloquio."""

import uuid

from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class ReservaEvaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "reserva_evaluacion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "evaluacion_id", "alumno_id",
            name="uq_reserva_evaluacion_tenant_evaluacion_alumno",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    evaluacion_id: Mapped[str] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alumno_id: Mapped[str] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha: Mapped[date] = mapped_column(
        Date, nullable=False,
    )
    hora: Mapped[str] = mapped_column(
        String(5), nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Activa",
    )

    evaluacion = relationship("Evaluacion", lazy="selectin")
    alumno = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ReservaEvaluacion(id={self.id}, estado={self.estado})>"
