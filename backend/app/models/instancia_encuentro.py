"""InstanciaEncuentro model — concrete encounter instance."""

import uuid

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class InstanciaEncuentro(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "instancia_encuentro"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slot_id: Mapped[str | None] = mapped_column(ForeignKey("slot_encuentro.id"), nullable=True)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Programado")
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    slot = relationship("SlotEncuentro", back_populates="instancias", lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
