## ADDED Requirements

### Requirement: Enrolar 2FA TOTP

El sistema SHALL proveer `POST /api/auth/2fa/enroll` que genere un secreto TOTP para el usuario autenticado y devuelva la URI de configuración (para Google Authenticator, Authy, etc.).

#### Scenario: Enrolar 2FA

- **WHEN** un usuario autenticado sin 2FA activo solicita enrolar
- **THEN** el sistema genera un secreto TOTP de 32 bytes, almacena el hash del secreto, y responde con la `otpauth://` URI y el secreto en Base32 (para mostrar como QR)

### Requirement: Verificar y activar 2FA

El sistema SHALL proveer `POST /api/auth/2fa/verify` que verifique un código TOTP y active el 2FA para el usuario.

#### Scenario: Verificación exitosa

- **WHEN** un usuario envía un código TOTP válido (6 dígitos) que coincide con su secreto
- **THEN** el sistema activa `2fa_enabled = true` y responde con HTTP 200

#### Scenario: Código inválido

- **WHEN** un usuario envía un código TOTP incorrecto
- **THEN** el sistema responde con HTTP 400

### Requirement: Gate 2FA en login

El sistema SHALL requerir verificación 2FA después de credenciales válidas si el usuario tiene 2FA habilitado, antes de emitir el JWT final.

#### Scenario: Flujo completo 2FA

- **WHEN** un usuario con 2FA pasa el paso de credenciales, obtiene un `session_token`, y luego envía ese token más un código TOTP válido
- **THEN** el sistema emite el access_token y refresh_token finales
