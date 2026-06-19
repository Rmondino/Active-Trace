"""RolPermiso model — many-to-many assignment of permissions to roles.

Each record assigns a permission to a role with an optional scope
(`propio` | `global`) that controls whether the permission requires
ownership verification.
"""

import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimeStampedMixin


class RolPermiso(Base, TimeStampedMixin):
    """Assignment of a permission to a role.

    Attributes:
        id: UUID primary key.
        rol_id: FK to the role.
        permiso_id: FK to the permission.
        alcance: Scope of the permission — `propio` (requires ownership check)
                 or `global` (no restrictions).
    """

    __tablename__ = "rol_permiso"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    rol_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("rol.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permiso_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("permiso.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alcance: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="global",
    )

    __table_args__ = (
        UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),
    )

    def __repr__(self) -> str:
        return f"<RolPermiso(rol_id={self.rol_id}, permiso_id={self.permiso_id}, alcance={self.alcance})>"
