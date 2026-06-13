## ADDED Requirements

### Requirement: Login con email y password

El sistema SHALL proveer un endpoint `POST /api/auth/login` que autentique al usuario mediante email y contraseña, utilizando Argon2id para verificación del hash.

#### Scenario: Login exitoso sin 2FA

- **WHEN** un usuario envía email y contraseña correctos, sin 2FA habilitado
- **THEN** el sistema responde con HTTP 200 y un body que contiene `access_token` (JWT, 15min), `refresh_token`, `token_type: "bearer"` y datos básicos del usuario

#### Scenario: Login con credenciales incorrectas

- **WHEN** un usuario envía email o contraseña incorrectos
- **THEN** el sistema responde con HTTP 401 y un mensaje genérico "Credenciales inválidas" (sin revelar si el email existe o no)

#### Scenario: Login con 2FA habilitado

- **WHEN** un usuario envía email y contraseña correctos, con 2FA habilitado
- **THEN** el sistema responde con HTTP 200, `requires_2fa: true` y un `session_token` temporal (5min) para completar el segundo factor

#### Scenario: Login con email inexistente

- **WHEN** un usuario envía un email que no está registrado en ningún tenant
- **THEN** el sistema responde con HTTP 401 y mensaje genérico "Credenciales inválidas"

### Requirement: Contraseña almacenada con Argon2id

El sistema SHALL almacenar las contraseñas utilizando Argon2id con parámetros seguros (memoria 19MB, iteraciones 2, paralelismo 1).

#### Scenario: Hash único por contraseña

- **WHEN** dos usuarios tienen la misma contraseña
- **THEN** sus hashes almacenados son diferentes (sal automática por hash)
