"""Liquidacion models — salarios, liquidaciones y facturas.

Modelos:
    - SalarioBase: salario base por rol
    - SalarioPlus: adicional por grupo
    - MateriaGrupoPlus: asociacion materia ↔ grupo plus
    - Liquidacion: liquidacion generada por docente
    - Factura: factura asociada a un docente
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class SalarioBase(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "salario_base"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    rol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)


class SalarioPlus(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "salario_plus"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    grupo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rol: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    tope_acumulacion: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )


class MateriaGrupoPlus(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "materia_grupo_plus"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    materia_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grupo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)


class Liquidacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "liquidacion"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    cohorte_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    comisiones: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    monto_base: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    monto_plus: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), default="Abierta", nullable=False
    )


class Factura(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "factura"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    tamano_kb: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=None
    )
    estado: Mapped[str] = mapped_column(
        String(20), default="Pendiente", nullable=False
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
