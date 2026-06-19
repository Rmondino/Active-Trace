"""Evaluacion model — convocatoria de coloquio/evaluacion."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Evaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "evaluacion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    materia_id: Mapped[str] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[str] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Coloquio",
    )
    instancia: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    dias_disponibles: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5,
    )
    cupo_por_dia: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10,
    )
    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
    )
    convocados: Mapped[list] = mapped_column(
        JSONB, default=list, nullable=False,
    )

    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Evaluacion(id={self.id}, instancia={self.instancia})>"
