"""User model — identity and authentication for all domain actors.

Every human using the system is a User within a tenant.
Roles and permissions are assigned via User.roles (JSONB list)
until C-04 RBAC formalizes the role-permission tables.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class User(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A user within a tenant.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        email: Login email (unique within tenant).
        password_hash: Argon2id hash of the password.
        2fa_secret: Encrypted TOTP secret (null if not enrolled).
        2fa_enabled: Whether 2FA is active.
        roles: JSONB list of role names (e.g. ["PROFESOR", "COORDINADOR"]).
    """

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    two_fa_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    two_fa_enabled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    roles: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
