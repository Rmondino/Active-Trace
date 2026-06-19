"""RefreshToken model — token rotation with family-based theft detection.

Each refresh token belongs to a "family". When a token is rotated,
if a used token from the same family is resubmitted, the entire
family is revoked (assumes token theft).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RefreshToken(Base):
    """A refresh token for a user session.

    Attributes:
        id: UUID primary key.
        user_id: FK to the owning user.
        token_hash: SHA-256 hash of the refresh token (never stored in plaintext).
        family: UUID that groups related refresh tokens (same session chain).
        expires_at: When this token expires.
        revoked_at: When this token was revoked (null if active).
        created_at: When this token was created.
    """

    __tablename__ = "refresh_token"

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
    family: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
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
    def is_revoked(self) -> bool:
        """Check if this token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if this token has expired."""
        return datetime.now(UTC) >= self.expires_at

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"
