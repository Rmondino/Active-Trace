## Why

El sistema necesita un flujo de autenticación seguro, multi-tenant y extensible como puerta de entrada a toda la plataforma. Sin este cimiento, ninguna operación protegida puede ejecutarse. Este change implementa el lado de autenticación (quién eres) dejando la autorización (qué puedes hacer) para C-04 RBAC.

## What Changes

- `POST /api/auth/login` — email + password con Argon2id, emite access token JWT (15min) + refresh token con rotación
- `POST /api/auth/refresh` — rota refresh token, emite nuevo par. Reuso del refresh invalida toda la sesión
- `POST /api/auth/logout` — revoca la sesión activa
- `POST /api/auth/2fa/enroll` — genera secreto TOTP para el usuario autenticado
- `POST /api/auth/2fa/verify` — verifica código TOTP y activa 2FA
- `POST /api/auth/forgot` — genera token de un solo uso por email, expiración 15min
- `POST /api/auth/reset` — canjea token + nueva contraseña
- Dependency `get_current_user` que resuelve identidad + tenant + roles desde el JWT verificado
- Rate limiting 5 intentos/60s por IP+email en login (en memoria)
- Modelos `User`, `RefreshToken`, `PasswordResetToken` en base de datos
- Regla de oro: identidad/tenant SOLO del JWT, jamás desde parámetros de petición

## Capabilities

### New Capabilities
- `auth-login`: Autenticación email+password con Argon2id, emisión de access token JWT
- `auth-refresh`: Refresh token rotation con invalidación por reuso, logout
- `auth-2fa`: TOTP opcional por usuario (enrolar, verificar, gate activo)
- `auth-password-recovery`: Recuperación de contraseña con token de un solo uso
- `auth-rate-limiting`: Rate limiting en login (5/60s por IP+email)
- `auth-session`: Dependency `get_current_user` que resuelve identidad desde JWT

### Modified Capabilities
- *(ninguna — C-03 introduce capabilities nuevas, no modifica existentes)*

## Impact

- **Nuevos endpoints**: 7 rutas en `routers/auth.py`
- **Nuevos modelos**: `User` (id, tenant_id, email, password_hash, 2fa_secret, 2fa_enabled), `RefreshToken` (id, user_id, token_hash, expires_at, family, revoked_at), `PasswordResetToken` (id, user_id, token_hash, expires_at, used_at)
- **Migración**: 002_create_user_auth_tables
- **Nuevo servicio**: `services/auth_service.py`
- **Nueva dependencia**: `core/dependencies.py` → `get_current_user` reemplaza el placeholder `get_tenant`
- **Dependencias externas**: `python-jose` (JWT), `pyotp` (TOTP), `argon2-cffi` (ya instalado)
- **Rate limit**: almacenamiento en memoria (diccionario compartido, OK para single-instance)
