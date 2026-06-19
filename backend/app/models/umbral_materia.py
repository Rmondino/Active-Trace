import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class UmbralMateria(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "umbral_materia"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    asignacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("asignacion.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    umbral_pct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )
    valores_aprobatorios: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: ["Satisfactorio", "Supera lo esperado"],
    )

    asignacion = relationship("Asignacion", lazy="selectin")
    materia = relationship("Materia", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uq_umbral_asignacion_materia",
        ),
        Index("ix_umbral_tenant_materia", "tenant_id", "materia_id"),
    )

    def __repr__(self) -> str:
        return f"<UmbralMateria(id={self.id}, umbral={self.umbral_pct}%)>"
