"""SlotEncuentro model — recurrence template for synchronous encounters."""

import uuid

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class SlotEncuentro(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "slot_encuentro"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asignacion_id: Mapped[str] = mapped_column(ForeignKey("asignacion.id"), nullable=False)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    dia_semana: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    cant_semanas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date] = mapped_column(Date, nullable=False)

    asignacion = relationship("Asignacion", lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
    instancias = relationship("InstanciaEncuentro", back_populates="slot", lazy="selectin")
