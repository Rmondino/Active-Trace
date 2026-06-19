"""ComentarioTarea model — comments on internal tasks."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class ComentarioTarea(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A comment on a Tarea."""

    __tablename__ = "comentario_tarea"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tarea_id: Mapped[str] = mapped_column(
        ForeignKey("tarea.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    autor_id: Mapped[str] = mapped_column(
        ForeignKey("user.id"), nullable=False,
    )
    texto: Mapped[str] = mapped_column(
        String(2000), nullable=False,
    )

    tarea = relationship("Tarea", lazy="selectin")
    autor = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ComentarioTarea(id={self.id}, tarea_id={self.tarea_id})>"
