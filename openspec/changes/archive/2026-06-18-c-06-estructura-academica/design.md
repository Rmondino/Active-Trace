## Context

Se parte de un proyecto con FastAPI async, SQLAlchemy 2.0, multi-tenancy row-level via `TenantScopedMixin`, soft delete via `SoftDeleteMixin`, repositorio genérico `BaseRepository` con filtro automático de tenant, y guard `require_permission` para RBAC. C-04 ya sembró el permiso `estructura:gestionar` con alcance `global` para el rol ADMIN.

No existe aún ningún modelo de dominio del negocio académico — solo infraestructura (Tenant, User, RBAC). Este change crea el primer piso del modelo de dominio.

## Goals / Non-Goals

**Goals:**
- Modelos `Carrera`, `Cohorte`, `Materia` con UUID PK, soft delete, tenant scope
- ABM completo (GET list, GET by id, POST create, PUT update, DELETE soft) bajo `/api/admin/carreras`, `/api/admin/cohortes`, `/api/admin/materias`
- Guard `require_permission("estructura:gestionar")` en todos los endpoints
- Unicidad `(tenant_id, codigo)` en Carrera y Materia; `(tenant_id, carrera_id, nombre)` en Cohorte
- Regla: carrera inactiva no admite cohortes con `vig_hasta` nulo (abiertas)
- Migración Alembic 004
- Tests: CRUD, unicidad por tenant, aislamiento multi-tenant, estado activa/inactiva

**Non-Goals:**
- No se crea la entidad `Asignacion` (será C-07)
- No se crean relaciones con otras entidades del dominio (calificaciones, encuentros, etc.)
- No hay endpoints públicos ni de consulta no administativa
- No hay importación masiva desde Moodle
- No hay endpoints de clonación de cohortes o carreras

## Decisions

| Decisión | Opción elegida | Alternativas | Razón |
|----------|---------------|--------------|-------|
| **Estructura de router** | Router único `admin/estructura.py` con tres secciones | Routers separados por entidad | Las tres entidades son pequeñas, mismo permiso, mismo namespace `/api/admin/`. Un solo archivo evita fragmentación prematura. Si crece, se separa. |
| **Repositorios** | Uno por entidad (`CarreraRepository`, `CohorteRepository`, `MateriaRepository`) heredando de `BaseRepository` | Repositorio único genérico | Cada entidad puede necesitar validaciones específicas (ej: `CohorteRepository` necesita verificar que la carrera esté activa). La herencia permite extender sin tocar el base. |
| **Validación de unicidad** | `Repository.exists_by(codigo=..., tenant_id=...)` antes de crear | UniqueConstraint + manejo de excepción | La constraint de DB existe como respaldo, pero el repo expone un check explícito para devolver 409 con mensaje claro. |
| **Regla carrera-inactiva** | En `CohorteRepository.create()` se verifica `carrera.estado == "Activa"` antes de permitir cohortes sin `vig_hasta` | Trigger de BD | La regla es de negocio, no de integridad referencial. Validarla en el repositorio (capa de dominio) es más explícito y testeable. |
| **Soft delete** | `DELETE` → `soft_delete()` del `BaseRepository` | Hard delete | Consistencia con el resto del proyecto (regla dura #13). |
| **Paginación** | `offset`/`limit` via `BaseRepository.list()` | Cursor-based | Consistente con el repositorio base existente. Se migrará a cursores si hay problemas de performance. |
| **Schemas Pydantic** | Request/Response por entidad en el router, con `extra='forbid'` | Schemas separados en archivo `schemas.py` | Los schemas son pequeños (<20 líneas cada uno). Inline en el router reduce archivos. Si crecen, se extraen. |

## Risks / Trade-offs

- **[Bajo] Crecimiento del router**: si los ABM crecen con filtros complejos o reportes, conviene separar en `admin/carreras.py`, `admin/cohortes.py`, `admin/materias.py`. Riesgo mitigado por la regla de ≤500 LOC/archivo.
- **[Bajo] Validación de unicidad duplicada**: la constraint de BD y el check en repo conviven. Si hay race condition, la BD rechaza el duplicado con un IntegrityError que se traduce a 409. Es un safety net, no una duplicación inútil.
- **[Medio] Sin paginación cursor-based**: `offset`/`limit` es frágil con tablas grandes. Para las magnitudes esperadas (decenas de carreras, centenas de cohortes/materias) no es problema. Se revisa en producción.
