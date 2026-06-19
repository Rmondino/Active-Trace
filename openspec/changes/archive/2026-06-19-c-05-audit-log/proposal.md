## Why

El nombre del producto es *trace*: todo se audita. Aunque ya tenemos un modelo AuditLog básico y se usa desde C-09, faltan capacidades críticas: impersonación, append-only enforcement, query de auditoría, y el campo `filas_afectadas`.

## What Changes

### AuditLog model — expandir
Agregar campos faltantes: `impersonado_id`, `user_agent`, `filas_afectadas`. La tabla debe ser **append-only**: sin UPDATE ni DELETE a nivel app.

### Impersonación (nuevo)
- Permiso `impersonacion:usar`
- `POST /api/auth/impersonar` — iniciar suplantación (requiere user_id destino)
- `POST /api/auth/dejar-impersonar` — finalizar
- Sesión distinguible en JWT (flag `impersonando: true`, `actor_original_id`)
- Auditoría: `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`

### Query de auditoría
- `GET /api/admin/auditoria` — listar logs con filtros (accion, materia_id, actor_id, desde, hasta, limit)
- Permiso: `auditoria:ver`

### Append-only enforcement
- Restricción a nivel app: el repositorio de AuditLog NO expone update() ni delete()
- En tests: verificar que intentar update/delete falle

### Migration
- Migración 013: expandir audit_log con campos faltantes, índices compuestos
