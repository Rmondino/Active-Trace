"""AuditLogService — centralized audit trail for domain actions."""

import uuid

from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, session):
        self.session = session

    async def log(
        self,
        actor_id: str,
        tenant_id: str,
        accion: str,
        materia_id: str | None = None,
        detalle: dict | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            tenant_id=tenant_id,
            accion=accion,
            materia_id=materia_id,
            detalle=detalle,
            ip=ip,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
