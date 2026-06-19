"""AuditLogService — centralized audit trail for domain actions."""

import uuid

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, session):
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        actor_id: str,
        tenant_id: str,
        accion: str,
        materia_id: str | None = None,
        detalle: dict | None = None,
        filas_afectadas: int | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        impersonado_id: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            tenant_id=tenant_id,
            accion=accion,
            materia_id=materia_id,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ip,
            user_agent=user_agent,
            impersonado_id=impersonado_id,
        )
        return await self.repo.create(entry)

    async def get_all(
        self,
        tenant_id: str,
        filtros: dict | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        return await self.repo.get_all(tenant_id, filtros, limit)
