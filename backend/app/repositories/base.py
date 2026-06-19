"""Generic base repository with tenant scope and soft delete.

All domain repositories should inherit from BaseRepository to get:
    - Automatic tenant_id filtering on all queries
    - Soft delete awareness (default-exclude deleted records)
    - Standard CRUD operations

Usage:
    class AlumnoRepository(BaseRepository[Alumno]):
        model_class = Alumno
        ...

    repo = AlumnoRepository(session=db, tenant_id="...")
    alumno = await repo.get(some_id)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mixins import SoftDeleteMixin, TenantScopedMixin

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Generic repository with tenant scope and soft delete.

    Type Parameters:
        ModelT: The SQLAlchemy model class this repository manages.

    Attributes:
        session: Async database session.
        tenant_id: Tenant ID used for automatic row-level filtering.
    """

    model_class: type[ModelT] | None = None

    def __init__(self, session: AsyncSession, tenant_id: str, model_class: type[ModelT] | None = None):
        """Initialize the repository with session and tenant scope.

        Args:
            session: Async SQLAlchemy session.
            tenant_id: Tenant UUID string for automatic filtering.
            model_class: Required model class. Can be set via subclass attribute or constructor argument.
        """
        self.session = session
        self.tenant_id = tenant_id
        resolved = model_class or self.model_class
        if resolved is None:
            raise TypeError(
                "BaseRepository.model_class must be set. Either set it as a "
                "class attribute on a subclass, or pass it to the constructor."
            )
        self.model_class = resolved

    def _apply_tenant_scope(self, stmt: Any) -> Any:
        """Apply tenant_id filter to a statement.

        Only applies if the model has TenantScopedMixin.
        """
        if hasattr(self.model_class, "tenant_id"):
            return stmt.where(self.model_class.tenant_id == self.tenant_id)  # type: ignore[union-attr]
        return stmt

    def _exclude_deleted(self, stmt: Any) -> Any:
        """Exclude soft-deleted records from a statement.

        Only applies if the model has SoftDeleteMixin.
        """
        if hasattr(self.model_class, "deleted_at"):
            return stmt.where(self.model_class.deleted_at.is_(None))  # type: ignore[union-attr]
        return stmt

    async def get(self, id: str) -> ModelT | None:
        """Get a record by ID, scoped to tenant and excluding soft-deleted.

        Args:
            id: UUID string of the record.

        Returns:
            The model instance or None if not found / belongs to other tenant.
        """
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.id == id)  # type: ignore[union-attr]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelT]:
        """List records with tenant scope, soft-delete exclusion, and optional filters.

        Args:
            offset: Query offset (pagination).
            limit: Maximum records to return.
            **filters: Keyword arguments matching model column names for equality filtering.

        Returns:
            List of model instances.
        """
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)

        for column_name, value in filters.items():
            column = getattr(self.model_class, column_name, None)
            if column is not None:
                stmt = stmt.where(column == value)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> ModelT:
        """Create a new record, automatically assigning tenant_id.

        Args:
            data: Dictionary of column values. tenant_id is set automatically
                  if the model has TenantScopedMixin.

        Returns:
            The created model instance.
        """
        if hasattr(self.model_class, "tenant_id"):
            data.setdefault("tenant_id", self.tenant_id)
        instance = self.model_class(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: str, data: dict[str, Any]) -> ModelT | None:
        """Update a record by ID, scoped to tenant.

        Args:
            id: UUID string of the record to update.
            data: Dictionary of column values to update.

        Returns:
            The updated model instance, or None if not found.
        """
        record = await self.get(id)
        if record is None:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def soft_delete(self, id: str) -> bool:
        """Soft-delete a record by ID (sets deleted_at timestamp).

        Only applies if the model has SoftDeleteMixin.
        Returns True if the record was found and deleted, False otherwise.
        """
        if not hasattr(self.model_class, "deleted_at"):
            return False

        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(deleted_at=datetime.now(UTC))
        )
        stmt = self._apply_tenant_scope(stmt)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def restore(self, id: str) -> bool:
        """Restore a soft-deleted record (clears deleted_at).

        Only applies if the model has SoftDeleteMixin.
        Returns True if the record was found and restored, False otherwise.
        """
        if not hasattr(self.model_class, "deleted_at"):
            return False

        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(deleted_at=None)
        )
        stmt = self._apply_tenant_scope(stmt)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def list_all(self) -> list[ModelT]:
        """List ALL records across tenants (skips tenant scope).

        WARNING: This intentionally bypasses tenant isolation.
        Only use in seeders, migrations, or admin operations
        where cross-tenant access is explicitly required.

        Still respects soft delete (excludes deleted records).
        """
        stmt = select(self.model_class)
        stmt = self._exclude_deleted(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
