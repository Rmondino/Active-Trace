## Migration 001 — create tenant table

### Requirement: Migración 001 — creación de tabla tenant

El sistema SHALL incluir una migración Alembic que cree la tabla `tenant` con los campos `id`, `slug`, `nombre`, `config` (JSONB), `estado`, `created_at`, `updated_at`.

#### Scenario: Tabla tenant existe

- **WHEN** se ejecuta `alembic upgrade head`
- **THEN** la tabla `tenant` existe en la base de datos con las columnas definidas
- **AND** `slug` tiene una constraint de unicidad

#### Scenario: Downgrade reversible

- **WHEN** se ejecuta `alembic downgrade -1`
- **THEN** la tabla `tenant` se elimina de la base de datos
