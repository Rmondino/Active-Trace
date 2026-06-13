"""Permiso model — atomic permission catalog for RBAC.

Each permiso represents a single capability expressed as `modulo:accion`
(e.g. "calificaciones:importar", "comunicacion:aprobar").
"""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimeStampedMixin


class Permiso(Base, TimeStampedMixin):
    """An atomic permission within the RBAC system.

    Attributes:
        id: UUID primary key.
        codigo: Unique permission code in `modulo:accion` format.
        descripcion: Human-readable description of what this permission grants.
    """

    __tablename__ = "permiso"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    codigo: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        return f"<Permiso(id={self.id}, codigo={self.codigo})>"
