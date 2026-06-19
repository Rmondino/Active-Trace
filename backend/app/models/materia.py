"""Materia model — subject/course catalog per tenant.

Represents a subject within the academic offering (e.g. "Programación I").
"""

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Materia(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A subject/course within a tenant.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        codigo: Short code unique per tenant (e.g. "PROG_I").
        nombre: Full subject name (e.g. "Programación I").
        estado: "Activa" or "Inactiva".
    """

    __tablename__ = "materia"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materia_tenant_codigo"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    codigo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Activa",
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Materia(id={self.id}, codigo={self.codigo})>"
