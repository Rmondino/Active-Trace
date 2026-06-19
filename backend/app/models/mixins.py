"""SQLAlchemy declarative mixins for all domain models.

Provides:
    - TimeStampedMixin: automatic created_at / updated_at
    - SoftDeleteMixin: nullable deleted_at for soft delete
    - TenantScopedMixin: tenant_id FK for multi-tenant isolation
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


class TimeStampedMixin:
    """Adds created_at and updated_at timestamp columns.

    Both are set automatically on INSERT; updated_at refreshes on UPDATE.
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            onupdate=lambda: datetime.now(UTC),
            nullable=False,
        )


class SoftDeleteMixin:
    """Adds a nullable deleted_at column for soft delete support.

    Active records have deleted_at = NULL.
    Soft-deleted records have deleted_at = timestamp.
    """

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(
            DateTime(timezone=True),
            default=None,
            nullable=True,
        )


class TenantScopedMixin:
    """Adds tenant_id FK column for multi-tenant row-level isolation.

    Every table that inherits this mixin MUST have a relationship
    to the Tenant model. The tenant_id is filtered automatically
    by BaseRepository.
    """

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(
            ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

    @declared_attr
    def tenant(cls):
        return relationship("Tenant", lazy="joined")
