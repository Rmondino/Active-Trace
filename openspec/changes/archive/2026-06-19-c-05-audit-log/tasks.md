# Tasks: C-05 audit-log

- [x] **1. Modelo**: Expandir AuditLog — add impersonado_id, user_agent, filas_afectadas
- [x] **2. Repositorio**: AuditLogRepository append-only (sin update/delete)
- [x] **3. AuditLogService**: Expandir log() con nuevos campos + get_all() con filtros
- [x] **4. Permiso seed**: Agregar auditoria:ver, impersonacion:usar
- [x] **5. Impersonación**: auth/impersonar + auth/dejar-impersonar endpoints
- [x] **6. JWT**: Expandir claims con actor_original_id, impersonando flag
- [x] **7. Router auditoría**: GET /api/admin/auditoria con filtros
- [x] **8. Migración 013**: Expandir audit_log table
- [x] **9. Tests**: append-only, log creation, impersonación, query, multi-tenant
- [x] **10. Safety Net + Archive + Engram Sync
