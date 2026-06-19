## ADDED Requirements

### Requirement: Endpoint de autenticación 2FA (POST /api/auth/2fa/authenticate)

El sistema SHALL proveer un endpoint público `POST /api/auth/2fa/authenticate` que reciba un `session_token` (JWT de la etapa 1 del login) y un código TOTP de 6 dígitos. Si el código es válido contra el `two_fa_secret` del usuario asociado al session_token, SHALL emitir el `access_token` y `refresh_token` finales y revocar el session_token.

#### Scenario: Autenticación 2FA exitosa

- **WHEN** un usuario envía un `session_token` vigente y un código TOTP válido de 6 dígitos
- **THEN** el sistema emite `access_token`, `refresh_token`, `token_type: "bearer"` y `user: { id }`
- **AND** el session_token queda invalidado

#### Scenario: Código TOTP inválido

- **WHEN** un usuario envía un código TOTP incorrecto
- **THEN** el sistema responde con HTTP 400 y mensaje "Código inválido"

#### Scenario: Session token inválido o expirado

- **WHEN** un usuario envía un `session_token` inválido o expirado
- **THEN** el sistema responde con HTTP 401 y mensaje "Sesión inválida o expirada"

## MODIFIED Requirements

### Requirement: Gate 2FA en login

El sistema SHALL requerir verificación 2FA después de credenciales válidas si el usuario tiene 2FA habilitado, antes de emitir el JWT final. El canje del `session_token` por los tokens finales se realiza mediante `POST /api/auth/2fa/authenticate`.

#### Scenario: Flujo completo 2FA

- **WHEN** un usuario con 2FA pasa el paso de credenciales, obtiene un `session_token`, y luego envía ese token más un código TOTP válido a `POST /api/auth/2fa/authenticate`
- **THEN** el sistema emite el access_token y refresh_token finales

### Requirement: Schemas de 2FA con extra='forbid'

Los schemas de request/response de 2fa SHALL incluir `model_config = ConfigDict(extra='forbid')` para rechazar campos no declarados.

#### Scenario: Extra fields en 2FA authenticate son rechazados

- **WHEN** un cliente envía campos adicionales no declarados en el schema de `Authenticate2FARequest`
- **THEN** el sistema responde con HTTP 422
