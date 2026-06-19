## ADDED Requirements

### Requirement: Solicitar recuperación de contraseña

El sistema SHALL proveer `POST /api/auth/forgot` que, dado un email, genere un token de un solo uso (válido 15 minutos) y lo almacene asociado al usuario. (El envío del email se integrará en C-12 comunicaciones; por ahora el token se devuelve en la respuesta para testing.)

#### Scenario: Solicitud de recuperación exitosa

- **WHEN** un usuario no autenticado envía un email registrado a `/api/auth/forgot`
- **THEN** el sistema genera un token criptográfico aleatorio, lo almacena con expiración de 15 minutos, y responde con HTTP 200 (mensaje genérico "Si el email está registrado, recibirás instrucciones")

#### Scenario: Solicitud con email no registrado

- **WHEN** un usuario envía un email no registrado
- **THEN** el sistema responde con HTTP 200 (mismo mensaje genérico, para no revelar qué emails existen)

### Requirement: Resetear contraseña

El sistema SHALL proveer `POST /api/auth/reset` que permita cambiar la contraseña usando un token de recuperación válido.

#### Scenario: Reset exitoso

- **WHEN** un usuario envía un token de recuperación válido y no expirado más una nueva contraseña que cumple los requisitos de seguridad
- **THEN** el sistema actualiza el password_hash, invalida el token (lo marca como usado), invalida todos los refresh tokens activos del usuario, y responde con HTTP 200

#### Scenario: Token inválido o expirado

- **WHEN** un usuario envía un token de recuperación inválido o expirado
- **THEN** el sistema responde con HTTP 400

#### Scenario: Token ya usado

- **WHEN** un usuario intenta usar un token de recuperación que ya fue canjeado
- **THEN** el sistema responde con HTTP 400
