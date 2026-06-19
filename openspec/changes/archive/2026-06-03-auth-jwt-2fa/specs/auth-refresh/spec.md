## ADDED Requirements

### Requirement: Refresh token con rotation

El sistema SHALL proveer `POST /api/auth/refresh` que rota el refresh token: invalida el actual y emite un nuevo par (access + refresh). Cada refresh token pertenece a una "familia" (family).

#### Scenario: Refresh exitoso

- **WHEN** un cliente envía un refresh token válido y no expirado
- **THEN** el sistema invalida ese refresh token, emite un nuevo access_token (15min) y un nuevo refresh_token, y responde con HTTP 200

#### Scenario: Reuso de refresh token (detección de robo)

- **WHEN** un cliente envía un refresh token que ya fue usado (invalidation_token coincide con un token ya gastado de la misma familia)
- **THEN** el sistema invalida TODA la familia de refresh tokens (revoca la sesión), y responde con HTTP 401

#### Scenario: Refresh con token expirado

- **WHEN** un cliente envía un refresh token cuyo `expires_at` ya pasó
- **THEN** el sistema responde con HTTP 401

### Requirement: Logout

El sistema SHALL proveer `POST /api/auth/logout` que revoque el refresh token activo.

#### Scenario: Logout exitoso

- **WHEN** un usuario autenticado envía su refresh token a `/api/auth/logout`
- **THEN** el sistema invalida ese refresh token y responde con HTTP 200

#### Scenario: Logout sin token

- **WHEN** un request no autenticado llama a `/api/auth/logout`
- **THEN** el sistema responde con HTTP 401
