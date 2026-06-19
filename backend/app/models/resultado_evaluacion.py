"""ResultadoEvaluacion model — nota final de un coloquio/evaluacion."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class ResultadoEvaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "resultado_evaluacion"

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
    nota_final: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    evaluacion = relationship("Evaluacion", lazy="selectin")
    alumno = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ResultadoEvaluacion(id={self.id}, nota={self.nota_final})>"
