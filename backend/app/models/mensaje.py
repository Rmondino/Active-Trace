"""Mensaje model — mensajería interna entre usuarios."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class Mensaje(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "mensaje"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    remitente_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("user.id"), nullable=False, index=True
    )
    destinatario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("user.id"), nullable=False, index=True
    )
    mensaje_padre_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("mensaje.id"), nullable=True
    )
    asunto: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    leido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    leido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
