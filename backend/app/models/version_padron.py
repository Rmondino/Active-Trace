"""VersionPadron model — a version of the student roster for a subject+cohort."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class VersionPadron(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "version_padron"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohorte.id"),
        nullable=False,
        index=True,
    )
    cargado_por: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id"),
        nullable=False,
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    activa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    origen: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    total_filas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
    cargador = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<VersionPadron(id={self.id}, materia={self.materia_id}, activa={self.activa})>"
