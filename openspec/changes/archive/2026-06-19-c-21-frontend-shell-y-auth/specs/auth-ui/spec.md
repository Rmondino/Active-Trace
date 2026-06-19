## ADDED Requirements

### Requirement: Pantalla de login

El sistema SHALL mostrar una pantalla de login con un formulario de email + password. Al enviar, SHALL llamar a `POST /api/auth/login`. Si las credenciales son válidas y no tiene 2FA, SHALL redirigir al dashboard. Si tiene 2FA, SHALL redirigir a la pantalla de 2FA. Si las credenciales son inválidas, SHALL mostrar error "Credenciales inválidas". Si hay rate limiting, SHALL mostrar "Demasiados intentos, intentá de nuevo en 60 segundos".

#### Scenario: Login exitoso sin 2FA

- **WHEN** el usuario ingresa credenciales válidas sin 2FA y envía el formulario
- **THEN** el sistema redirige al dashboard (`/`) con access_token y refresh_token almacenados

#### Scenario: Login exitoso con 2FA

- **WHEN** el usuario ingresa credenciales válidas con 2FA habilitado y envía el formulario
- **THEN** el sistema redirige a `/login/2fa` con el session_token recibido

#### Scenario: Credenciales inválidas

- **WHEN** el usuario ingresa email o password incorrectos
- **THEN** el sistema muestra "Credenciales inválidas" sin revelar cuál campo es incorrecto

#### Scenario: Loading state durante submit

- **WHEN** el usuario envía el formulario y la petición está en curso
- **THEN** el botón de submit muestra un spinner y está deshabilitado

#### Scenario: Validación de campos en cliente

- **WHEN** el usuario ingresa un email con formato inválido o deja campos vacíos
- **THEN** el sistema muestra errores de validación en el cliente antes de enviar la petición

### Requirement: Pantalla de 2FA (autenticación)

El sistema SHALL mostrar una pantalla de ingreso de código TOTP de 6 dígitos cuando el login requiera 2FA. SHALL enviar el código + session_token a `POST /api/auth/2fa/authenticate`. Si es válido, SHALL emitir los tokens finales y redirigir al dashboard.

#### Scenario: Código 2FA válido

- **WHEN** el usuario ingresa un código TOTP válido de 6 dígitos y el session_token es vigente
- **THEN** el sistema recibe access_token + refresh_token y redirige al dashboard

#### Scenario: Código 2FA inválido

- **WHEN** el usuario ingresa un código TOTP incorrecto
- **THEN** el sistema muestra "Código inválido"

#### Scenario: Session token expirado

- **WHEN** el session_token ha expirado (pasaron más de 15 minutos desde el login)
- **THEN** el sistema redirige a `/login` con mensaje "Tu sesión expiró, iniciá sesión de nuevo"

### Requirement: Pantalla de configuración de 2FA (enroll)

El sistema SHALL permitir al usuario autenticado configurar 2FA desde `/2fa/setup`. SHALL mostrar un QR code (generado con la URI `otpauth://`) y el secreto en texto para ingreso manual. SHALL pedir verificar un código TOTP para activar el 2FA.

#### Scenario: Enroll 2FA exitoso

- **WHEN** un usuario autenticado sin 2FA navega a `/2fa/setup`
- **THEN** se muestra un QR code y un campo para verificar código TOTP

#### Scenario: Activación de 2FA

- **WHEN** el usuario ingresa un código TOTP válido en la pantalla de setup
- **THEN** el sistema activa 2FA y muestra mensaje "2FA activado exitosamente"

### Requirement: Pantalla de recuperación de contraseña (forgot)

El sistema SHALL mostrar un formulario donde el usuario ingresa su email para solicitar un token de recuperación. SHALL llamar a `POST /api/auth/forgot`. Siempre SHALL mostrar el mismo mensaje ("Si el email está registrado, recibirás instrucciones") independientemente de si el email existe o no, para evitar enumeración de usuarios.

#### Scenario: Solicitud de recuperación

- **WHEN** el usuario ingresa un email y envía el formulario
- **THEN** el sistema muestra "Si el email está registrado, recibirás instrucciones"

### Requirement: Pantalla de reseteo de contraseña (reset)

El sistema SHALL mostrar un formulario donde el usuario ingresa su nueva contraseña (más confirmación) y el token recibido por email. SHALL llamar a `POST /api/auth/reset`. Si el token es válido, SHALL redirigir al login con mensaje de éxito. Si es inválido/expirado, SHALL mostrar error.

#### Scenario: Reset exitoso

- **WHEN** el usuario ingresa una contraseña válida y un token de reset vigente
- **THEN** el sistema redirige a `/login` con mensaje "Contraseña actualizada exitosamente"

#### Scenario: Token inválido o expirado

- **WHEN** el usuario ingresa un token inválido o expirado
- **THEN** el sistema muestra "El enlace de recuperación es inválido o expiró"

#### Scenario: Validación de contraseña en cliente

- **WHEN** el usuario ingresa una contraseña de menos de 8 caracteres o las contraseñas no coinciden
- **THEN** el sistema muestra errores de validación antes de enviar la petición

### Requirement: Logout

El sistema SHALL proveer un botón de cerrar sesión que llame a `POST /api/auth/logout` con el refresh_token, limpie el estado de sesión y redirija a `/login`.

#### Scenario: Logout exitoso

- **WHEN** el usuario autenticado hace clic en "Cerrar sesión"
- **THEN** el sistema llama a `POST /api/auth/logout`, limpia el estado de sesión y redirige a `/login`
