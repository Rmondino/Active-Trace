# Spec: audit-log

### REQ-AUD-001: Append-only
**Scenario:** AuditLogRepository no tiene update() ni delete()
**Scenario:** Intentar UPDATE/SET en audit_log falla a nivel app

### REQ-AUD-002: Log creation
**Scenario:** Crear log con actor_id, accion, materia_id, detalle, ip
**Scenario:** Crear log con filas_afectadas y user_agent
**Scenario:** Crear log con impersonado_id

### REQ-AUD-003: Impersonación
**Scenario:** POST /api/auth/impersonar devuelve JWT con actor_original_id
**Scenario:** POST /api/auth/impersonar sin permiso → 403
**Scenario:** POST /api/auth/impersonar usuario inexistente → 404
**Scenario:** POST /api/auth/dejar-impersonar restaura JWT original
**Scenario:** Al impersonar se registra IMPERSONACION_INICIAR
**Scenario:** Al dejar impersonar se registra IMPERSONACION_FINALIZAR

### REQ-AUD-004: Query auditoría
**Scenario:** GET /api/admin/auditoria lista logs del tenant
**Scenario:** Filtrar por accion
**Scenario:** Filtrar por materia_id
**Scenario:** Filtrar por rango de fechas
**Scenario:** 403 sin permiso auditoria:ver
**Scenario:** Multi-tenant isolation
