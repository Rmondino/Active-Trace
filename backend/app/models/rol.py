"""Rol model — domain role catalog for RBAC.

Each Rol represents a function (e.g. PROFESOR, COORDINADOR).
Permissions are assigned to roles via RolPermiso (many-to-many).
"""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimeStampedMixin


class Rol(Base, TimeStampedMixin, SoftDeleteMixin):
    """A domain role within a tenant.

    Attributes:
        id: UUID primary key.
        slug: URL-safe unique identifier (e.g. "profesor").
        nombre: Human-readable role name (e.g. "PROFESOR").
        descripcion: Optional description of the role.
        is_domain_role: Whether this is a system domain role (cannot be deleted).
    """

    __tablename__ = "rol"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    is_domain_role: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Rol(id={self.id}, slug={self.slug})>"
