"""EntradaPadron model — a single student entry within a roster version."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class EntradaPadron(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "entrada_padron"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("version_padron.id"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id"),
        nullable=True,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    apellidos: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    comision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    regional: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    version = relationship("VersionPadron", lazy="selectin")
    usuario = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<EntradaPadron(id={self.id}, version={self.version_id})>"
