"""Carrera model — academic career/course catalog per tenant.

Represents a degree program or career track within an institution.
"""

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Carrera(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """An academic career within a tenant.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        codigo: Short code unique per tenant (e.g. "TUPAD").
        nombre: Full career name (e.g. "Tecnicatura ...").
        estado: "Activa" or "Inactiva".
    """

    __tablename__ = "carrera"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carrera_tenant_codigo"),
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
        return f"<Carrera(id={self.id}, codigo={self.codigo})>"
