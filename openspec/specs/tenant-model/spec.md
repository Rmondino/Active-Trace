## Tenant model — root entity

### Requirement: Modelo Tenant como entidad raíz

El sistema SHALL tener una entidad `Tenant` que represente cada institución. `Tenant` es la raíz del modelo de datos y no tiene `tenant_id` propia.

#### Scenario: Creación de un tenant

- **WHEN** se crea un nuevo tenant con slug y nombre válidos
- **THEN** el tenant se persiste con `id` UUID, `slug` único, `nombre`, `config` JSONB y `estado` Activo

#### Scenario: Slug único a nivel global

- **WHEN** se intenta crear un tenant con un slug ya existente
- **THEN** la operación falla por violación de unicidad

### Requirement: Mixins ORM base

El sistema SHALL proveer tres mixins SQLAlchemy que toda tabla de dominio hereda: `TimeStampedMixin` (created_at, updated_at), `SoftDeleteMixin` (deleted_at nullable), y `TenantScopedMixin` (tenant_id FK).

#### Scenario: Timestamps automáticos

- **WHEN** se crea un nuevo registro de cualquier modelo de dominio
- **THEN** `created_at` y `updated_at` se setean automáticamente con la hora UTC actual
- **AND** `updated_at` se actualiza en cada modificación

#### Scenario: Soft delete

- **WHEN** se invoca soft_delete sobre un registro activo
- **THEN** el registro mantiene `deleted_at` con timestamp (no se elimina físicamente)
- **AND** el registro deja de aparecer en queries de lectura estándar

#### Scenario: Restore de soft delete

- **WHEN** se invoca restore sobre un registro soft-deleteado
- **THEN** `deleted_at` se setea a NULL
- **AND** el registro vuelve a aparecer en queries de lectura estándar

### Requirement: Modelo Base con UUID PK

El sistema SHALL tener una clase `Base` declarativa que combine los tres mixins y agregue `id` como UUID PK con generación automática.

#### Scenario: ID automático en creación

- **WHEN** se crea un modelo que hereda de `Base`
- **THEN** el campo `id` se genera automáticamente como UUID v4
