## ADDED Requirements

### Requirement: ADMIN can create users with PII
The system SHALL allow ADMIN users to create new users with full profile data including encrypted PII fields.

#### Scenario: Create user successfully
- **WHEN** an ADMIN sends a POST to `/api/admin/usuarios` with valid `UserCreate` data
- **THEN** the system SHALL return 201 with `UserDetail` including the new user's data
- **AND** the PII fields (email, dni, cuil, cbu, alias_cbu) SHALL be encrypted with AES-256-GCM at rest
- **AND** the email_hash SHALL be stored as SHA-256(LOWER(email))

#### Scenario: Create user with duplicate email
- **WHEN** an ADMIN sends a POST to `/api/admin/usuarios` with an email that already exists in the same tenant
- **THEN** the system SHALL return 409 Conflict

#### Scenario: Create user without permission
- **WHEN** a user without `usuarios:gestionar` permission sends a POST to `/api/admin/usuarios`
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Create user rejects extra fields
- **WHEN** an ADMIN sends a POST with undeclared fields
- **THEN** the system SHALL return 422 with validation error (extra='forbid')

### Requirement: ADMIN can list users with masked PII
The system SHALL allow ADMIN users to list all users in their tenant. PII fields SHALL be masked in list responses.

#### Scenario: List users returns masked PII
- **WHEN** an ADMIN sends a GET to `/api/admin/usuarios`
- **THEN** the system SHALL return 200 with a list of `UserRead` objects
- **AND** each user SHALL have email, dni, cuil, cbu fields masked (e.g., "j***@example.com", "*********123")

#### Scenario: List filters by search query
- **WHEN** an ADMIN sends a GET to `/api/admin/usuarios?search=term`
- **THEN** the system SHALL return users matching by nombre, apellidos, legajo, or email

#### Scenario: List filters by estado
- **WHEN** an ADMIN sends a GET to `/api/admin/usuarios?estado=Inactivo`
- **THEN** the system SHALL return only users with estado "Inactivo"

#### Scenario: List is tenant-isolated
- **WHEN** an ADMIN of tenant A lists users
- **THEN** the system SHALL NOT return users from tenant B

### Requirement: ADMIN can read user detail with full PII
The system SHALL allow ADMIN users to read a specific user's full profile with decrypted PII.

#### Scenario: Read user detail returns full PII
- **WHEN** an ADMIN sends a GET to `/api/admin/usuarios/{id}`
- **THEN** the system SHALL return 200 with `UserDetail` including decrypted email, dni, cuil, cbu

#### Scenario: Read non-existent user returns 404
- **WHEN** an ADMIN sends a GET to `/api/admin/usuarios/{non_existent_id}`
- **THEN** the system SHALL return 404 Not Found

### Requirement: ADMIN can update users
The system SHALL allow ADMIN users to update user profile data.

#### Scenario: Update user data
- **WHEN** an ADMIN sends a PUT to `/api/admin/usuarios/{id}` with valid `UserUpdate` data
- **THEN** the system SHALL return 200 with updated `UserDetail`
- **AND** modified PII fields SHALL be re-encrypted

#### Scenario: Update non-existent user returns 404
- **WHEN** an ADMIN sends a PUT to `/api/admin/usuarios/{non_existent_id}`
- **THEN** the system SHALL return 404 Not Found

### Requirement: ADMIN can soft-delete users
The system SHALL allow ADMIN users to soft-delete (deactivate) users.

#### Scenario: Delete user returns 204
- **WHEN** an ADMIN sends a DELETE to `/api/admin/usuarios/{id}`
- **THEN** the system SHALL return 204 No Content
- **AND** the user SHALL have deleted_at set

#### Scenario: Deleted user not visible in list
- **WHEN** an ADMIN lists users after deleting one
- **THEN** the deleted user SHALL NOT appear in the list
