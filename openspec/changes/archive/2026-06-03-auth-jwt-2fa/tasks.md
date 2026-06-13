## 1. Modelos de datos y migración

- [x] 1.1 Crear `models/user.py` con User (id UUID, tenant_id FK, email, password_hash, 2fa_secret, 2fa_enabled, roles JSONB, timestamps, soft delete)
- [x] 1.2 Crear `models/refresh_token.py` con RefreshToken (id, user_id FK, token_hash, family UUID, expires_at, created_at, revoked_at nullable)
- [x] 1.3 Crear `models/password_reset_token.py` con PasswordResetToken (id, user_id FK, token_hash, expires_at, used_at nullable, created_at)
- [x] 1.4 Generar migración Alembic 002 con las tres tablas (user, refresh_token, password_reset_token)
- [x] 1.5 Ejecutar `alembic upgrade head` y verificar tablas

## 2. Utilidades JWT (core/jwt.py)

- [x] 2.1 Implementar `create_access_token(user, settings) -> str` con claims: sub, tenant_id, roles, exp (15min), iat, jti
- [x] 2.2 Implementar `create_refresh_token(user, settings) -> str` con exp 7 días
- [x] 2.3 Implementar `verify_token(token, settings) -> dict` que valida firma + exp
- [x] 2.4 Implementar `decode_token_unsafe(token) -> dict` para debugging (sin verificación)
- [x] 3.1 Implementar `hash_password(plain: str) -> str` con Argon2id
- [x] 3.2 Implementar `verify_password(plain: str, hashed: str) -> bool`

## 4. Auth service (services/auth_service.py)

- [x] 4.1 Implementar `authenticate(db, email, password) -> User | None`
- [x] 4.2 Implementar `login(db, email, password) -> dict` (maneja gate 2FA, emite tokens)
- [x] 4.3 Implementar `refresh_access(db, refresh_token_str) -> dict` (rotation + detección de reuso)
- [x] 4.4 Implementar `logout(db, refresh_token_str) -> None`
- [x] 4.5 Implementar `enroll_2fa(user) -> dict` (genera secreto TOTP, devuelve URI)
- [x] 4.6 Implementar `verify_2fa(user, code) -> bool` (verifica código y activa 2FA)
- [x] 4.7 Implementar `complete_2fa_login(db, session_token, code) -> dict` (emite tokens post-2FA)
- [x] 4.8 Implementar `create_password_reset_token(db, email) -> str | None`
- [x] 4.9 Implementar `reset_password(db, token_str, new_password) -> bool`
- [x] 5.1 Implementar `RateLimiter` clase con ventana deslizante en memoria
- [x] 5.2 Implementar `check(key: str, max_attempts=5, window_seconds=60) -> bool`
- [x] 5.3 Implementar dependencia FastAPI `rate_limit_login` (extrae IP + email)

## 6. Routers (routers/auth.py)

- [x] 6.1 Implementar `POST /api/auth/login` con rate-limiting y gate 2FA
- [x] 6.2 Implementar `POST /api/auth/refresh` con rotation y detección de reuso
- [x] 6.3 Implementar `POST /api/auth/logout` con revocación
- [x] 6.4 Implementar `POST /api/auth/2fa/enroll` (requiere autenticación)
- [x] 6.5 Implementar `POST /api/auth/2fa/verify` (verifica código y activa)
- [x] 6.6 Implementar `POST /api/auth/forgot` (solicitar recuperación)
- [x] 6.7 Implementar `POST /api/auth/reset` (canjear token + nueva password)
- [x] 6.8 Registrar router en `app/main.py`

## 7. Dependencias de sesión

- [x] 7.1 Implementar `get_current_user` en `core/current_user.py` (verifica JWT, resuelve User)
- [x] 7.2 Actualizar `get_tenant` para obtener tenant_id desde JWT claims
- [x] 7.3 Agregar `require_2fa` dependency para el gate de 2FA

## 8. Tests

- [x] 8.1 (TDD) Tests de JWT utils: create + verify round-trip, token expirado, firma inválida
- [x] 8.2 (TDD) Tests de password hashing: hash + verify, contraseña incorrecta falla
- [x] 8.3 (TDD) Tests de rate limiter: dentro del límite, excedido, ventana deslizante
- [x] 8.4 (TDD) Tests de login: OK, KO, con 2FA gate, con email inexistente
- [x] 8.5 (TDD) Tests de refresh rotation: OK, reuso invalida familia, expirado
- [x] 8.6 (TDD) Tests de 2FA: enroll, verify, código incorrecto
- [x] 8.7 (TDD) Tests de password recovery: forgot, reset, token inválido, token reusado
- [x] 8.8 (TDD) Tests de get_current_user: token válido, expirado, sin tenant_id, user inexistente
- [x] 8.9 Ejecutar suite completa y confirmar verde
