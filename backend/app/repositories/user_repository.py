"""UserRepository — CRUD for User model with tenant scope and PII search."""

from sqlalchemy import select, func, or_

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with tenant-scoped queries."""

    model_class = User

    async def get_by_email_hash(self, tenant_id: str, email_hash: str) -> User | None:
        """Get a user by their email_hash within a tenant.

        Args:
            tenant_id: The tenant UUID.
            email_hash: SHA-256 hash of the lowercased email.

        Returns:
            User or None if not found.
        """
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.email_hash == email_hash,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_legajo(self, tenant_id: str, legajo: str) -> User | None:
        """Get a user by their legajo within a tenant.

        Args:
            tenant_id: The tenant UUID.
            legajo: The student/employee file number.

        Returns:
            User or None if not found.
        """
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.legajo == legajo,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, tenant_id: str, query: str) -> list[User]:
        """Search users by nombre, apellidos, or legajo (partial match).

        Args:
            tenant_id: The tenant UUID.
            query: Search term.

        Returns:
            List of matching User instances.
        """
        pattern = f"%{query}%"
        stmt = select(User).where(
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
            or_(
                User.nombre.ilike(pattern),
                User.apellidos.ilike(pattern),
                User.legajo.ilike(pattern),
                User.email_hash.ilike(pattern),
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_email_hash(
        self, tenant_id: str, email_hash: str, exclude_id: str | None = None
    ) -> bool:
        """Check if a user with the given email_hash exists in this tenant.

        Args:
            tenant_id: The tenant UUID.
            email_hash: SHA-256 hash of the lowercased email.
            exclude_id: Optional user ID to exclude (for update scenarios).

        Returns:
            True if a user with this email_hash exists.
        """
        stmt = select(func.count()).select_from(User)
        stmt = stmt.where(
            User.tenant_id == tenant_id,
            User.email_hash == email_hash,
            User.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
