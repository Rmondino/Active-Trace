## ADDED Requirements

### Requirement: Catálogo de Carreras

El sistema SHALL mantener un catálogo de carreras (tabla `carrera`) por tenant con: `id` (UUID PK), `tenant_id` (FK), `codigo` (texto único por tenant, ej: "TUPAD"), `nombre` (texto, ej: "Tecnicatura Universitaria en Programación y Administración de Datos"), `estado` (texto: "Activa" | "Inactiva"). Soporta soft delete y timestamps.

#### Scenario: ADMIN lista carreras
- **WHEN** un ADMIN ejecuta `GET /api/admin/carreras`
- **THEN** el sistema retorna la lista de carreras activas del tenant (excluye soft-deleted)

#### Scenario: ADMIN crea carrera exitosamente
- **WHEN** un ADMIN ejecuta `POST /api/admin/carreras` con `codigo` y `nombre` válidos
- **THEN** el sistema crea la carrera con `estado="Activa"` y retorna 201

#### Scenario: Carrera con código duplicado es rechazada
- **WHEN** un ADMIN intenta crear una carrera con un `codigo` que ya existe en el mismo tenant
- **THEN** el sistema retorna 409 Conflict con detalle "El código ya existe"

#### Scenario: ADMIN actualiza carrera
- **WHEN** un ADMIN ejecuta `PUT /api/admin/carreras/{id}` con nuevos valores de `nombre` o `estado`
- **THEN** el sistema actualiza la carrera y retorna 200

#### Scenario: ADMIN elimina carrera (soft delete)
- **WHEN** un ADMIN ejecuta `DELETE /api/admin/carreras/{id}`
- **THEN** el sistema marca la carrera como eliminada (soft delete) y retorna 204

#### Scenario: Carrera de otro tenant no es visible
- **WHEN** un ADMIN consulta carreras de otro tenant
- **THEN** el sistema no retorna esas carreras (aislamiento multi-tenant)

### Requirement: Catálogo de Cohortes

El sistema SHALL mantener un catálogo de cohortes (tabla `cohorte`) por tenant con: `id` (UUID PK), `tenant_id` (FK), `carrera_id` (FK), `nombre` (texto, ej: "MAR-2026"), `anio` (entero), `vig_desde` (fecha), `vig_hasta` (fecha nullable = cohorte abierta), `estado` (texto: "Activa" | "Inactiva"). Unicidad por `(tenant_id, carrera_id, nombre)`. Soporta soft delete y timestamps.

#### Scenario: ADMIN lista cohortes
- **WHEN** un ADMIN ejecuta `GET /api/admin/cohortes`
- **THEN** el sistema retorna la lista de cohortes activas del tenant (excluye soft-deleted)

#### Scenario: ADMIN filtra cohortes por carrera
- **WHEN** un ADMIN ejecuta `GET /api/admin/cohortes?carrera_id={id}`
- **THEN** el sistema retorna solo las cohortes de esa carrera

#### Scenario: ADMIN crea cohorte exitosamente
- **WHEN** un ADMIN ejecuta `POST /api/admin/cohortes` con `carrera_id`, `nombre`, `anio` y `vig_desde` válidos
- **THEN** el sistema crea la cohorte con `estado="Activa"` y retorna 201

#### Scenario: Cohorte duplicada es rechazada
- **WHEN** un ADMIN intenta crear una cohorte con el mismo `nombre` para la misma `carrera_id` en el mismo tenant
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Cohorte abierta en carrera inactiva es rechazada
- **WHEN** un ADMIN intenta crear una cohorte sin `vig_hasta` (abierta) para una carrera con `estado="Inactiva"`
- **THEN** el sistema retorna 400 con detalle "No se pueden crear cohortes abiertas para una carrera inactiva"

#### Scenario: Cohorte cerrada en carrera inactiva es permitida
- **WHEN** un ADMIN intenta crear una cohorte con `vig_hasta` definida (cerrada) para una carrera con `estado="Inactiva"`
- **THEN** el sistema crea la cohorte exitosamente

#### Scenario: ADMIN actualiza cohorte
- **WHEN** un ADMIN ejecuta `PUT /api/admin/cohortes/{id}` con nuevos valores
- **THEN** el sistema actualiza la cohorte y retorna 200

#### Scenario: ADMIN elimina cohorte (soft delete)
- **WHEN** un ADMIN ejecuta `DELETE /api/admin/cohortes/{id}`
- **THEN** el sistema marca la cohorte como eliminada y retorna 204

#### Scenario: Cohorte de otro tenant no es visible
- **WHEN** un ADMIN consulta cohortes de otro tenant
- **THEN** el sistema no retorna esas cohortes

### Requirement: Catálogo de Materias

El sistema SHALL mantener un catálogo de materias (tabla `materia`) por tenant con: `id` (UUID PK), `tenant_id` (FK), `codigo` (texto único por tenant, ej: "PROG_I"), `nombre` (texto, ej: "Programación I"), `estado` (texto: "Activa" | "Inactiva"). Soporta soft delete y timestamps.

#### Scenario: ADMIN lista materias
- **WHEN** un ADMIN ejecuta `GET /api/admin/materias`
- **THEN** el sistema retorna la lista de materias activas del tenant (excluye soft-deleted)

#### Scenario: ADMIN crea materia exitosamente
- **WHEN** un ADMIN ejecuta `POST /api/admin/materias` con `codigo` y `nombre` válidos
- **THEN** el sistema crea la materia con `estado="Activa"` y retorna 201

#### Scenario: Materia con código duplicado es rechazada
- **WHEN** un ADMIN intenta crear una materia con un `codigo` que ya existe en el mismo tenant
- **THEN** el sistema retorna 409 Conflict

#### Scenario: ADMIN actualiza materia
- **WHEN** un ADMIN ejecuta `PUT /api/admin/materias/{id}` con nuevos valores de `nombre` o `estado`
- **THEN** el sistema actualiza la materia y retorna 200

#### Scenario: ADMIN elimina materia (soft delete)
- **WHEN** un ADMIN ejecuta `DELETE /api/admin/materias/{id}`
- **THEN** el sistema marca la materia como eliminada y retorna 204

#### Scenario: Materia de otro tenant no es visible
- **WHEN** un ADMIN consulta materias de otro tenant
- **THEN** el sistema no retorna esas materias

### Requirement: Protección con permiso estructura:gestionar

Todos los endpoints de `/api/admin/carreras`, `/api/admin/cohortes` y `/api/admin/materias` SHALL estar protegidos con el guard `require_permission("estructura:gestionar")`.

#### Scenario: ADMIN con permiso accede
- **WHEN** un ADMIN (que tiene permiso `estructura:gestionar`) ejecuta cualquier endpoint de estructura académica
- **THEN** el sistema permite el acceso

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin permiso `estructura:gestionar` intenta acceder a cualquier endpoint de estructura académica
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Aislamiento multi-tenant

Todas las operaciones de estructura académica SHALL estar acotadas al tenant del usuario autenticado. Ningún query puede cruzar datos entre tenants.

#### Scenario: Datos de tenant A no afectan a tenant B
- **WHEN** un ADMIN del tenant A crea una carrera y un ADMIN del tenant B lista carreras
- **THEN** el ADMIN de B no ve la carrera creada por A
