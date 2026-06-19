"""AuditoriaMetricsService — aggregation queries for the auditoria dashboard.

Provides analytics over AuditLog and Comunicacion tables.
No new models — all queries are read-only aggregations.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditoriaMetricsService:
    """Aggregation queries over AuditLog/Comunicacion for the auditoria panel."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def acciones_por_dia(
        self,
        tenant_id: str,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: str | None = None,
    ) -> list[dict]:
        stmt = select(
            func.date(AuditLog.created_at).label("dia"),
            func.count(AuditLog.id).label("total"),
        ).where(AuditLog.tenant_id == tenant_id)
        if desde:
            stmt = stmt.where(AuditLog.created_at >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.created_at <= hasta + timedelta(days=1))
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.group_by("dia").order_by("dia")
        result = await self.session.execute(stmt)
        return [{"dia": str(row.dia), "total": row.total} for row in result]

    async def comunicaciones_por_docente(self, tenant_id: str) -> list[dict]:
        from app.models.comunicacion import Comunicacion

        stmt = select(
            Comunicacion.enviado_por,
            Comunicacion.estado,
            func.count(Comunicacion.id).label("total"),
        ).where(
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.deleted_at.is_(None),
        ).group_by(Comunicacion.enviado_por, Comunicacion.estado)
        result = await self.session.execute(stmt)
        return [
            {"usuario_id": r.enviado_por, "estado": r.estado, "total": r.total}
            for r in result
        ]

    async def interacciones_por_docente_materia(
        self,
        tenant_id: str,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        actor_id: str | None = None,
    ) -> list[dict]:
        stmt = select(
            AuditLog.actor_id,
            AuditLog.materia_id,
            AuditLog.accion,
            func.count(AuditLog.id).label("total"),
        ).where(AuditLog.tenant_id == tenant_id)
        if desde:
            stmt = stmt.where(AuditLog.created_at >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.created_at <= hasta + timedelta(days=1))
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.group_by(AuditLog.actor_id, AuditLog.materia_id, AuditLog.accion)
        result = await self.session.execute(stmt)
        return [
            {"actor_id": r.actor_id, "materia_id": r.materia_id, "accion": r.accion, "total": r.total}
            for r in result
        ]

    async def ultimas_acciones(
        self,
        tenant_id: str,
        limit: int = 200,
        actor_id: str | None = None,
    ) -> list[dict]:
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._log_to_dict(l) for l in result.scalars().all()]

    async def log_completo(
        self,
        tenant_id: str,
        filtros: dict | None = None,
        limit: int = 200,
    ) -> list[dict]:
        from app.services.audit_log_service import AuditLogService

        audit_svc = AuditLogService(self.session)
        logs = await audit_svc.get_all(tenant_id, filtros, limit)
        return [self._log_to_dict(l) for l in logs]

    def _log_to_dict(self, l: AuditLog) -> dict:
        return {
            "id": l.id,
            "actor_id": l.actor_id,
            "accion": l.accion,
            "materia_id": l.materia_id,
            "detalle": l.detalle,
            "filas_afectadas": l.filas_afectadas,
            "ip": l.ip,
            "user_agent": l.user_agent,
            "created_at": l.created_at.isoformat(),
        }
