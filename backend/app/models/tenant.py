"""Tenant model — root entity for multi-tenant isolation.

Each tenant represents an institution. All domain data is scoped
by tenant_id. Tenant itself does NOT have a tenant_id (it IS the tenant).
"""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimeStampedMixin


class Tenant(Base, TimeStampedMixin, SoftDeleteMixin):
    """An institution (multi-tenant root).

    Attributes:
        id: UUID primary key.
        slug: URL-safe unique identifier (e.g. "universidad-nacional").
        nombre: Human-readable institution name.
        config: JSONB blob for tenant-specific configuration.
        estado: Active or Inactive.
        created_at: Inherited from TimeStampedMixin.
        updated_at: Inherited from TimeStampedMixin.
        deleted_at: Inherited from SoftDeleteMixin.
    """

    __tablename__ = "tenant"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    config: Mapped[dict | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Activo",
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, slug={self.slug})>"
