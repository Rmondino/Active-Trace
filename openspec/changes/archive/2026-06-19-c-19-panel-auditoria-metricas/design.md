## Servicio: AuditoriaMetricsService

```python
class AuditoriaMetricsService:
    def __init__(self, session, tenant_id):
        self.session = session
        self.tenant_id = tenant_id
    
    async def acciones_por_dia(self, desde: date | None, hasta: date | None, 
                                actor_id: str | None = None) -> list[dict]:
        """Agrupa audit_log por día, cuenta acciones."""
        stmt = select(
            func.date(AuditLog.created_at).label('dia'),
            func.count(AuditLog.id).label('total'),
        ).where(
            AuditLog.tenant_id == self.tenant_id,
        )
        if desde:
            stmt = stmt.where(AuditLog.created_at >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.created_at <= hasta + timedelta(days=1))
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.group_by('dia').order_by('dia')
        result = await self.session.execute(stmt)
        return [{"dia": row.dia.isoformat(), "total": row.total} for row in result]
    
    async def comunicaciones_por_docente(self) -> list[dict]:
        """Agrupa comunicaciones por enviado_por y estado."""
        from app.models.comunicacion import Comunicacion
        stmt = select(
            Comunicacion.enviado_por,
            Comunicacion.estado,
            func.count(Comunicacion.id).label('total'),
        ).where(
            Comunicacion.tenant_id == self.tenant_id,
            Comunicacion.deleted_at.is_(None),
        ).group_by(Comunicacion.enviado_por, Comunicacion.estado)
        result = await self.session.execute(stmt)
        return [{"usuario_id": row.enviado_por, "estado": row.estado, "total": row.total} for row in result]
    
    async def interacciones_por_docente_materia(self, desde=None, hasta=None, actor_id=None) -> list[dict]:
        """Agrupa audit_log por actor y materia."""
        stmt = select(
            AuditLog.actor_id,
            AuditLog.materia_id,
            AuditLog.accion,
            func.count(AuditLog.id).label('total'),
        ).where(AuditLog.tenant_id == self.tenant_id)
        if desde:
            stmt = stmt.where(AuditLog.created_at >= desde)
        if hasta:
            stmt = stmt.where(AuditLog.created_at <= hasta + timedelta(days=1))
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.group_by(AuditLog.actor_id, AuditLog.materia_id, AuditLog.accion)
        result = await self.session.execute(stmt)
        return [{"actor_id": r.actor_id, "materia_id": r.materia_id, "accion": r.accion, "total": r.total} for r in result]
    
    async def ultimas_acciones(self, limit: int = 200, actor_id: str | None = None) -> list[dict]:
        """Últimas N acciones."""
        stmt = select(AuditLog).where(AuditLog.tenant_id == self.tenant_id)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        return [self._log_to_dict(l) for l in logs]
    
    async def log_completo(self, filtros: dict, limit: int = 200) -> list[dict]:
        """Log completo con filtros (F9.2). Reuses AuditLogService.get_all()."""
        from app.services.audit_log_service import AuditLogService
        audit_svc = AuditLogService(self.session)
        logs = await audit_svc.get_all(self.tenant_id, filtros, limit)
        return [self._log_to_dict(l) for l in logs]
    
    def _log_to_dict(self, l: AuditLog) -> dict:
        return {
            "id": l.id, "actor_id": l.actor_id, "accion": l.accion,
            "materia_id": l.materia_id, "detalle": l.detalle,
            "filas_afectadas": l.filas_afectadas, "ip": l.ip,
            "user_agent": l.user_agent, "created_at": l.created_at.isoformat(),
        }
```

## Router

Mover/crear en `routers/auditoria.py`:

```python
router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])

@router.get("/acciones-por-dia", dependencies=[Depends(require_permission("auditoria:ver"))])
async def acciones_por_dia(...)

@router.get("/comunicaciones-por-docente", dependencies=[Depends(require_permission("auditoria:ver"))])
async def comunicaciones_por_docente(...)

@router.get("/interacciones-por-docente-materia", dependencies=[Depends(require_permission("auditoria:ver"))])
async def interacciones(...)

@router.get("/ultimas-acciones", dependencies=[Depends(require_permission("auditoria:ver"))])
async def ultimas_acciones(...)

@router.get("/log", dependencies=[Depends(require_permission("auditoria:ver"))])
async def log_completo(...)
```

**Scope control**: Si el usuario es COORDINADOR, los endpoints filtran por `actor_id = current_user.id` (scope propio). Si es ADMIN, ve todo.

## Tests

- acciones_por_dia: agrupa correctamente
- comunicaciones_por_docente: estados agregados
- interacciones: agrupación por user×materia
- ultimas_acciones: límite configurable
- log_completo: filtros funcionan
- Scope propio: COORDINADOR ve solo sus datos
- 403 sin auditoria:ver
- Multi-tenant
