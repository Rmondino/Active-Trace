## ADDED Requirements

### Requirement: Repository genérico con tenant scope

El sistema SHALL proveer una clase `BaseRepository[ModelT]` genérica que implemente CRUD básico con filtro automático de tenant_id y soft delete.

#### Scenario: Get con scope de tenant

- **WHEN** se invoca `get(id)` desde un repositorio con un tenant_id específico
- **THEN** la query filtra por `id`, `tenant_id` y `deleted_at IS NULL`
- **AND** si el registro pertenece a otro tenant, retorna None

#### Scenario: List con scope de tenant

- **WHEN** se invoca `list()` desde un repositorio
- **THEN** la query filtra por `tenant_id` y `deleted_at IS NULL`

#### Scenario: Create asigna tenant_id automático

- **WHEN** se invoca `create(data)`
- **THEN** el tenant_id del repositorio se asigna automáticamente al modelo (el data no necesita incluirlo)

#### Scenario: Update con scope

- **WHEN** se invoca `update(id, data)` con un ID que pertenece al tenant
- **THEN** el registro se actualiza
- **AND** si el ID pertenece a otro tenant, no se modifica

#### Scenario: Soft delete

- **WHEN** se invoca `soft_delete(id)`
- **THEN** el registro se marca con `deleted_at` (no se elimina)
- **AND** el registro deja de aparecer en get/list

#### Scenario: Restore

- **WHEN** se invoca `restore(id)` sobre un registro soft-deleteado
- **THEN** `deleted_at` se setea a NULL
- **AND** el registro vuelve a aparecer en get/list

#### Scenario: list_all salta scope de tenant

- **WHEN** se invoca `list_all()`
- **THEN** retorna registros de todos los tenants (sin filtro de tenant_id)
- **AND** respeta soft delete (no retorna borrados)
