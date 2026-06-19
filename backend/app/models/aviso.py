"""Aviso model — notice/tablón board with scope, severity, and acknowledgment support."""

import uuid

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Aviso(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A notice/announcement visible to users based on scope and vigencia.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        alcance: Visibility scope — Global, PorMateria, PorCohorte, PorRol.
        materia_id: Optional FK to materia (for PorMateria scope).
        cohorte_id: Optional FK to cohorte (for PorCohorte scope).
        rol_destino: Optional role slug (for PorRol scope).
        severidad: Severity level — Info, Advertencia, Critico.
        titulo: Short title (max 200 chars).
        cuerpo: Full body content (max 5000 chars).
        inicio_en: Start of visibility window.
        fin_en: End of visibility window.
        orden: Display order (higher = more priority).
        activo: Whether the notice is active.
        requiere_ack: Whether acknowledgment is required.
    """

    __tablename__ = "aviso"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    alcance: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default="Global",
    )
    materia_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    cohorte_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohorte.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    rol_destino: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None,
    )
    severidad: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Info",
    )
    titulo: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        String(5000), nullable=False,
    )
    inicio_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    fin_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    orden: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
    )
    requiere_ack: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
    )

    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Aviso(id={self.id}, titulo={self.titulo})>"
