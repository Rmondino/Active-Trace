## Why

C-05 implementó el audit log como infraestructura. C-19 construye el **panel de auditoría y métricas** sobre ese audit log: acciones por día, estado de comunicaciones por docente, interacciones, y log consultable. Sin esto, los datos de auditoría existen pero no son visibles para los administradores.

## What Changes

### Analytics endpoints (sin modelos nuevos)

| Método | Ruta | Descripción | Scope |
|--------|------|-------------|-------|
| `GET` | `/api/auditoria/acciones-por-dia` | Acciones agregadas por día | global/propio |
| `GET` | `/api/auditoria/comunicaciones-por-docente` | Estados de comunicación por docente | global |
| `GET` | `/api/auditoria/interacciones-por-docente-materia` | Interacciones por user×materia | global/propio |
| `GET` | `/api/auditoria/ultimas-acciones` | Últimas N acciones (defecto 200) | global/propio |
| `GET` | `/api/auditoria/log` | Log completo con filtros (F9.2) | global |

### Permiso
- `auditoria:ver` — ya existe de C-05
- Scope `(propio)`: COORDINADOR ve solo sus acciones
- Scope global: ADMIN ve todo

### Filtros
- rango de fechas (`desde`, `hasta`)
- materia
- usuario/actor
- acción
- estado (para comunicaciones)
- límite configurable
