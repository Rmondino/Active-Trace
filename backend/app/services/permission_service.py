"""Permission resolution service — RBAC authorization server-side.

Resolves effective permissions for a user within a tenant by:
    1. Finding all roles assigned to the user
    2. Union of all permissions from those roles (via rol_permiso)
    3. Returning (codigo, alcance) tuples scoped by tenant

The User.roles JSONB is used as a source of role slugs for the user.
Permissions are NEVER cached in the JWT — always resolved server-side.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.user import User


class PermissionService:
    """Service for resolving effective permissions for users.

    Args:
        db: Database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_effective_permissions(
        self,
        user: User,
    ) -> list[tuple[str, str]]:
        """Get all effective permissions for a user within their tenant.

        Resolves the union of permissions from all roles assigned to the user.

        Args:
            user: The user (must have .roles and .tenant_id).

        Returns:
            List of (codigo, alcance) tuples.
            Empty list if the user has no roles.
        """
        if not user.roles:
            return []

        # Find role IDs by slug
        result = await self.db.execute(
            select(Rol.id).where(
                Rol.slug.in_(user.roles),
                Rol.deleted_at.is_(None),
            )
        )
        role_ids = [row[0] for row in result.all()]
        if not role_ids:
            return []

        # Get all permissions for these roles
        result = await self.db.execute(
            select(Permiso.codigo, RolPermiso.alcance)
            .select_from(RolPermiso)
            .join(Permiso, Permiso.id == RolPermiso.permiso_id)
            .where(RolPermiso.rol_id.in_(role_ids))
        )

        # Deduplicate by codigo (union of permissions)
        seen: set[str] = set()
        permissions: list[tuple[str, str]] = []
        for codigo, alcance in result.all():
            if codigo not in seen:
                seen.add(codigo)
                permissions.append((codigo, alcance))

        return permissions

    async def has_permission(
        self,
        user: User,
        codigo: str,
    ) -> bool:
        """Check if a user has a specific permission.

        Args:
            user: The user.
            codigo: Permission code in `modulo:accion` format.

        Returns:
            True if the user has the permission.
        """
        permissions = await self.get_effective_permissions(user)
        return any(p[0] == codigo for p in permissions)

    async def get_permission_scope(
        self,
        user: User,
        codigo: str,
    ) -> str | None:
        """Get the scope of a specific permission for the user.

        Args:
            user: The user.
            codigo: Permission code.

        Returns:
            'propio', 'global', or None if the user doesn't have the permission.
        """
        permissions = await self.get_effective_permissions(user)
        for perm_codigo, alcance in permissions:
            if perm_codigo == codigo:
                return alcance
        return None
