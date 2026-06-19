"""PasswordResetToken model — single-use recovery tokens.

Each token is valid for 15 minutes and can only be used once.
The token itself is never stored in plaintext — only its SHA-256 hash.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PasswordResetToken(Base):
    """A single-use password reset token.

    Attributes:
        id: UUID primary key.
        user_id: FK to the owning user.
        token_hash: SHA-256 hash of the reset token (never stored in plaintext).
        expires_at: When this token expires (15 minutes from creation).
        used_at: When this token was used (null if unused).
        created_at: When this token was created.
    """

    __tablename__ = "password_reset_token"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    @property
    def is_used(self) -> bool:
        """Check if this token has been used."""
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if this token has expired."""
        return datetime.now(UTC) >= self.expires_at

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"
