## ADDED Requirements

### Requirement: Resolución de identidad desde JWT

El sistema SHALL proveer una dependencia FastAPI `get_current_user` que verifique el JWT en el header `Authorization: Bearer <token>`, extraiga los claims (`user_id`, `tenant_id`, `roles`), y resuelva el usuario desde la base de datos.

#### Scenario: Token válido

- **WHEN** un request incluye un JWT válido y no expirado en el header Authorization
- **THEN** `get_current_user` retorna el objeto User correspondiente con sus datos

#### Scenario: Token expirado

- **WHEN** un request incluye un JWT cuyo `exp` ya pasó
- **THEN** `get_current_user` lanza HTTP 401

#### Scenario: Token inválido

- **WHEN** un request incluye un JWT con firma inválida
- **THEN** `get_current_user` lanza HTTP 401

#### Scenario: Token sin tenant_id

- **WHEN** un request incluye un JWT válido pero sin el claim `tenant_id`
- **THEN** `get_current_user` lanza HTTP 401

#### Scenario: Token con user_id que no existe en BD

- **WHEN** un request incluye un JWT válido pero el `user_id` no corresponde a ningún usuario activo
- **THEN** `get_current_user` lanza HTTP 401

### Requirement: get_tenant como derivado de get_current_user

El sistema SHALL actualizar `get_tenant` (de C-02) para que obtenga el `tenant_id` desde `get_current_user` en lugar de consultar la base de datos.

#### Scenario: Tenant desde sesión

- **WHEN** cualquier endpoint protegido usa `get_tenant`
- **THEN** el tenant_id se extrae del JWT del usuario autenticado, no de una query a la BD

### Requirement: Claims mínimos del JWT

El sistema SHALL incluir en todo JWT emitido los siguientes claims:
- `sub`: user_id (UUID)
- `tenant_id`: tenant_id del usuario
- `roles`: lista de roles del usuario
- `exp`: expiración (epoch)
- `iat`: emitido en (epoch)
- `jti`: identificador único del token (UUID v4)

#### Scenario: JWT contiene todos los claims

- **WHEN** se decodifica un JWT emitido por el sistema
- **THEN** contiene `sub`, `tenant_id`, `roles`, `exp`, `iat` y `jti`
