"""Comunicacion model — communication/email records with state machine."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Comunicacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "comunicacion"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    enviado_por: Mapped[str] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
    )
    materia_id: Mapped[str] = mapped_column(
        ForeignKey("materia.id"),
        nullable=False,
        index=True,
    )
    destinatario: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendiente",
    )
    lote_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )
    error_msg: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    aprobado_por: Mapped[str | None] = mapped_column(
        ForeignKey("user.id"),
        nullable=True,
    )
    aprobado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    enviador = relationship("User", foreign_keys=[enviado_por], lazy="selectin")
    aprobador = relationship("User", foreign_keys=[aprobado_por], lazy="selectin")
    materia = relationship("Materia", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Comunicacion(id={self.id}, estado={self.estado}, lote={self.lote_id})>"
