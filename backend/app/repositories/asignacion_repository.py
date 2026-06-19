"""AsignacionRepository — CRUD for Asignacion model with vigencia filtering."""

from datetime import date

from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Repository for Asignacion entity with tenant-scoped queries."""

    model_class = Asignacion

    def _apply_vigencia_filter(self, stmt, *, fecha: date | None = None) -> None:
        """Apply vigencia condition to a statement (mutates in-place).

        Args:
            stmt: The SQL statement to modify.
            fecha: Reference date (defaults to today).
        """
        ref = fecha or date.today()
        stmt.where(
            Asignacion.desde <= ref,
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
        )

    async def get_vigentes(
        self, tenant_id: str, fecha: date | None = None
    ) -> list[Asignacion]:
        """Get all vigentes (active) asignaciones for a tenant.

        Args:
            tenant_id: The tenant UUID.
            fecha: Reference date (defaults to today).

        Returns:
            List of vigentes Asignacion instances.
        """
        ref = fecha or date.today()
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= ref,
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_usuario(
        self, tenant_id: str, usuario_id: str, solo_vigentes: bool = True
    ) -> list[Asignacion]:
        """Get asignaciones for a specific user.

        Args:
            tenant_id: The tenant UUID.
            usuario_id: The user UUID.
            solo_vigentes: If True, only return active asignaciones.

        Returns:
            List of Asignacion instances.
        """
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
        )
        if solo_vigentes:
            ref = date.today()
            stmt = stmt.where(
                Asignacion.desde <= ref,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_materia(
        self, tenant_id: str, materia_id: str, solo_vigentes: bool = True
    ) -> list[Asignacion]:
        """Get asignaciones for a specific materia.

        Args:
            tenant_id: The tenant UUID.
            materia_id: The materia UUID.
            solo_vigentes: If True, only return active asignaciones.

        Returns:
            List of Asignacion instances.
        """
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.materia_id == materia_id,
            Asignacion.deleted_at.is_(None),
        )
        if solo_vigentes:
            ref = date.today()
            stmt = stmt.where(
                Asignacion.desde <= ref,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_rol(
        self, tenant_id: str, rol: str, solo_vigentes: bool = True
    ) -> list[Asignacion]:
        """Get asignaciones by role name.

        Args:
            tenant_id: The tenant UUID.
            rol: Role name (e.g. "PROFESOR").
            solo_vigentes: If True, only return active asignaciones.

        Returns:
            List of Asignacion instances.
        """
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.rol == rol,
            Asignacion.deleted_at.is_(None),
        )
        if solo_vigentes:
            ref = date.today()
            stmt = stmt.where(
                Asignacion.desde <= ref,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_role_slugs(
        self, tenant_id: str, usuario_id: str
    ) -> list[str]:
        """Get unique, lowercased role slugs from active asignaciones.

        This is used by PermissionService to resolve permissions.

        Args:
            tenant_id: The tenant UUID.
            usuario_id: The user UUID.

        Returns:
            List of lowercased unique role slugs (e.g. ["profesor", "coordinador"]).
        """
        ref = date.today()
        stmt = select(Asignacion.rol).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= ref,
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref),
        )
        result = await self.session.execute(stmt)
        return list(set(row[0].lower() for row in result.all()))
