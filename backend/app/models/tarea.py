"""Tarea model — internal task assignment with state machine."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin

VALID_TRANSITIONS_TAREA: dict[str, set[str]] = {
    "Pendiente": {"En progreso", "Cancelada"},
    "En progreso": {"Resuelta", "Cancelada"},
}


def validar_transicion_tarea(actual: str, nuevo: str) -> None:
    if actual not in VALID_TRANSITIONS_TAREA:
        raise ValueError(f"Estado terminal '{actual}': no permite transiciones")
    if nuevo not in VALID_TRANSITIONS_TAREA[actual]:
        raise ValueError(f"Transición inválida: {actual} → {nuevo}")


class Tarea(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """An internal task assigned to a user within a tenant."""

    __tablename__ = "tarea"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    materia_id: Mapped[str | None] = mapped_column(
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True, default=None,
    )
    asignado_a: Mapped[str] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True,
    )
    asignado_por: Mapped[str] = mapped_column(
        ForeignKey("user.id"), nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente",
    )
    descripcion: Mapped[str] = mapped_column(
        String(5000), nullable=False,
    )
    contexto_id: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None,
    )

    asignado = relationship("User", foreign_keys=[asignado_a], lazy="selectin")
    asignador = relationship("User", foreign_keys=[asignado_por], lazy="selectin")
    materia = relationship("Materia", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Tarea(id={self.id}, estado={self.estado})>"
