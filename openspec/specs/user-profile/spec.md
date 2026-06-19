## ADDED Requirements

### Requirement: Authenticated user can view own profile
The system SHALL allow any authenticated user to view their own full profile, including decrypted PII.

#### Scenario: Get own profile
- **WHEN** an authenticated user sends a GET to `/api/usuarios/me`
- **THEN** the system SHALL return 200 with `UserDetail` containing decrypted email, dni, cuil, cbu
- **AND** the response SHALL include nombre, apellidos, legajo, regional, estado

#### Scenario: Unauthenticated request returns 401
- **WHEN** a request without a valid JWT is sent to `/api/usuarios/me`
- **THEN** the system SHALL return 401 Unauthorized

### Requirement: Authenticated user can view own active asignaciones
The system SHALL allow any authenticated user to list their own active asignaciones.

#### Scenario: Get my active asignaciones
- **WHEN** an authenticated user sends a GET to `/api/usuarios/me/asignaciones`
- **THEN** the system SHALL return 200 with a list of active `AsignacionRead` objects
- **AND** only vigentes asignaciones SHALL be returned
