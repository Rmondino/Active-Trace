## ADDED Requirements

### Requirement: Coordinator can create asignaciones
The system SHALL allow users with `equipos:asignar` permission (COORDINADOR, ADMIN) to create asignaciones that link a user to a role and academic context.

#### Scenario: Create asignacion successfully
- **WHEN** a COORDINADOR sends a POST to `/api/asignaciones` with valid `AsignacionCreate` data
- **THEN** the system SHALL return 201 with the created asignacion
- **AND** the `estado_vigencia` SHALL be "Vigente" if today is within `[desde, hasta)`

#### Scenario: Create asignacion with vencida state
- **WHEN** a COORDINADOR creates an asignacion with `hasta` before today
- **THEN** the `estado_vigencia` SHALL be "Vencida"

#### Scenario: Create asignacion without permission
- **WHEN** a user without `equipos:asignar` sends a POST to `/api/asignaciones`
- **THEN** the system SHALL return 403 Forbidden

### Requirement: Users can list asignaciones with filters
The system SHALL allow listing asignaciones filterable by usuario_id, materia_id, rol, and vigencia status.

#### Scenario: List asignaciones filtered by usuario
- **WHEN** a COORDINADOR sends a GET to `/api/asignaciones?usuario_id={id}`
- **THEN** the system SHALL return all asignaciones for that user

#### Scenario: List only vigentes
- **WHEN** a COORDINADOR sends a GET to `/api/asignaciones?solo_vigentes=true`
- **THEN** the system SHALL return only asignaciones where `desde <= hoy AND (hasta IS NULL OR hasta >= hoy)`

#### Scenario: List asignaciones is tenant-isolated
- **WHEN** a user lists asignaciones
- **THEN** the system SHALL NOT return asignaciones from other tenants

### Requirement: Users can read, update, and delete asignaciones
The system SHALL support full CRUD for asignaciones with soft delete.

#### Scenario: Read asignacion detail
- **WHEN** a COORDINADOR sends a GET to `/api/asignaciones/{id}`
- **THEN** the system SHALL return the asignacion with its derived `estado_vigencia`

#### Scenario: Update asignacion vigencia
- **WHEN** a COORDINADOR sends a PUT to `/api/asignaciones/{id}` with new dates
- **THEN** the system SHALL update and return the modified asignacion

#### Scenario: Delete asignacion
- **WHEN** a COORDINADOR sends a DELETE to `/api/asignaciones/{id}`
- **THEN** the system SHALL return 204 No Content (soft delete)

### Requirement: PermissionService resolves roles from Asignacion
The system SHALL resolve effective permissions from active Asignacion records, NOT from the deprecated JSONB `roles` column.

#### Scenario: PermissionService finds roles from active asignaciones
- **WHEN** resolving permissions for a user with active `PROFESOR` asignacion
- **THEN** the system SHALL return permissions for the PROFESOR role

#### Scenario: Vencida asignacion does not grant permissions
- **WHEN** resolving permissions for a user whose only asignacion is vencida
- **THEN** the system SHALL return an empty permission list

#### Scenario: Multi-role union of permissions
- **WHEN** a user has both PROFESOR and COORDINADOR active asignaciones
- **THEN** the system SHALL return the union of both roles' permissions (deduplicated)
