## Why

La plataforma necesita un catálogo de estructura académica (carreras, cohortes, materias) como base para todos los módulos del dominio: equipos docentes, calificaciones, comunicaciones, encuentros, liquidaciones. Sin estas entidades raíz, ningún otro módulo puede operar con contexto académico. Este change crea el primer piso del dominio después de la infraestructura de tenants y RBAC.

## What Changes

- Nuevos modelos SQLAlchemy: `Carrera`, `Cohorte`, `Materia` con soft delete y tenant scope
- ABM completo (`GET list`, `GET by id`, `POST create`, `PUT update`, `DELETE soft`) para los tres recursos bajo `/api/admin/`
- Protección de todos los endpoints con el permiso `estructura:gestionar` (rol ADMIN)
- Reglas de unicidad: `(tenant_id, codigo)` en Carrera y Materia; `(tenant_id, carrera_id, nombre)` en Cohorte
- Regla de negocio: carrera inactiva no admite cohortes con `vig_hasta` nulo (abiertas)
- Migración Alembic 004 con las tres tablas
- Tests de CRUD, unicidad por tenant, aislamiento multi-tenant, estado activa/inactiva

## Capabilities

### New Capabilities
- `estructura-academica-abm`: ABM multi-tenant de Carrera, Cohorte y Materia con guard `estructura:gestionar`, validaciones de unicidad, soft delete, y regla carrera-inactiva-no-cohortes-abiertas

### Modified Capabilities
*(ninguna — es el primer módulo de dominio sobre la infraestructura de tenants y RBAC)*

## Impact

- **Backend**: nuevos modelos, servicios, repositorios, router y schemas Pydantic en `backend/app/models/`, `backend/app/repositories/`, `backend/app/services/`, `backend/app/routers/admin/`
- **Migraciones**: nueva migración 004 en `backend/alembic/versions/`
- **Permisos**: el permiso `estructura:gestionar` ya existe en el seed de C-04, no requiere cambios
- **Tenant scope**: todas las queries filtran por `tenant_id` automáticamente vía `BaseRepository`
- **Tests**: nuevo módulo de tests para estructura académica en `backend/tests/`
