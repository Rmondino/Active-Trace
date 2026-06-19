"""Guardia model — duty shift record."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Guardia(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "guardia"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asignacion_id: Mapped[str] = mapped_column(ForeignKey("asignacion.id"), nullable=False)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    carrera_id: Mapped[str | None] = mapped_column(ForeignKey("carrera.id"), nullable=True)
    cohorte_id: Mapped[str | None] = mapped_column(ForeignKey("cohorte.id"), nullable=True)
    dia: Mapped[str] = mapped_column(String(10), nullable=False)
    horario: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendiente")
    comentarios: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    asignacion = relationship("Asignacion", lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
    carrera = relationship("Carrera", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
