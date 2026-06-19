"""User model — identity and profile for all domain actors.

Every human using the system is a User within a tenant.
Roles are derived from Asignacion records (not stored in User).
PII fields (email, dni, cuil, cbu, alias_cbu) are AES-256-GCM encrypted.
email_hash stores SHA-256(LOWER(email)) for login lookup.
"""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


class User(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    """A user within a tenant.

    Attributes:
        id: UUID primary key.
        tenant_id: FK to the owning tenant.
        email_hash: SHA-256(LOWER(email)) for login lookup.
        email: AES-256-GCM encrypted email.
        password_hash: Argon2id hash of the password.
        two_fa_secret: Encrypted TOTP secret (null if not enrolled).
        two_fa_enabled: Whether 2FA is active.
        nombre: First name.
        apellidos: Last name / surname.
        dni: AES-256-GCM encrypted national ID.
        cuil: AES-256-GCM encrypted tax ID (optional).
        cbu: AES-256-GCM encrypted bank account (optional).
        alias_cbu: AES-256-GCM encrypted bank alias (optional).
        banco: Bank name (optional).
        regional: Regional / location (optional).
        legajo: Student/employee file number (optional — business attribute).
        legajo_profesional: Professional license number (optional).
        facturador: Whether user is a biller (default False).
        estado: "Activo" or "Inactivo" (default "Activo").
    """

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
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
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    apellidos: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    dni: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    cuil: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=None,
    )
    cbu: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=None,
    )
    alias_cbu: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=None,
    )
    banco: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    regional: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    legajo: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    legajo_profesional: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    facturador: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="Activo",
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email_hash={self.email_hash})>"
