"""AuditLogRepository — APPEND-ONLY repository for audit trail.

No update(), no delete(), no soft_delete().
This repository does NOT inherit from BaseRepository (which has update/soft_delete).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """APPEND-ONLY repository. No update, no delete, no soft delete."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entry: AuditLog) -> AuditLog:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get(self, id: str) -> AuditLog | None:
        stmt = select(AuditLog).where(AuditLog.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        tenant_id: str,
        filtros: dict | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if filtros:
            if filtros.get("accion"):
                stmt = stmt.where(AuditLog.accion == filtros["accion"])
            if filtros.get("materia_id"):
                stmt = stmt.where(AuditLog.materia_id == filtros["materia_id"])
            if filtros.get("actor_id"):
                stmt = stmt.where(AuditLog.actor_id == filtros["actor_id"])
            if filtros.get("desde"):
                stmt = stmt.where(AuditLog.created_at >= filtros["desde"])
            if filtros.get("hasta"):
                stmt = stmt.where(AuditLog.created_at <= filtros["hasta"])
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
