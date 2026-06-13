## Context

Actualmente el sistema tiene un placeholder `get_tenant` en `core/tenancy.py` que retorna el primer tenant activo. No hay autenticación real — cualquier request es aceptada. C-03 reemplaza esto con autenticación JWT completa: login, refresh rotation, 2FA opcional, recuperación de contraseña y rate limiting.

La identidad se resuelve exclusivamente del JWT verificado. El tenant_id viaja dentro del JWT como claim estándar. La sesión es la fuente única de verdad para identidad, tenant y roles (estos últimos se usarán en C-04 RBAC).

## Goals / Non-Goals

**Goals:**
- Login con email + password (Argon2id), JWT access 15min + refresh token con rotation
- Logout que revoca la sesión
- 2FA TOTP opcional por usuario
- Recuperación de contraseña con token de un solo uso
- Rate limiting 5 intentos/60s por IP+email en login
- Dependency `get_current_user` que reemplaza `get_tenant`
- Modelos User, RefreshToken, PasswordResetToken
- Todos los claims mínimos de seguridad: user_id, tenant_id, roles, exp, iat, jti

**Non-Goals:**
- Autorización (permisos finos `modulo:accion`) — será C-04
- Catálogo de roles administrable — será C-04
- Multi-session (ventanas simultáneas) — por ahora una sesión activa a la vez
- Rate limiting persistente (BD/Redis) — en memoria, suficiente para single-instance early stage

## Decisions

### D1: JWT con algoritmo RS256 vs HS256
**Decisión**: HS256 con `SECRET_KEY`.
**Rationale**: Mientras no haya múltiples servicios que necesiten verificar tokens sin compartir secreto, HS256 es más simple. Migrar a RS256 en el futuro si hay microservicios.
**Alternativa**: RS256 requeriría gestionar par de llaves desde el inicio, sobreingeniería para esta etapa.

### D2: Refresh token rotation con detector de reuso
**Decisión**: Cada refresh emite un nuevo par (access + refresh). El refresh anterior se invalida. Si un refresh ya usado se reenvía, se invalida toda la familia (familly) — asume robo.
**Rationale**: Es el estándar OAuth2 para refresh rotation (RFC 6749 §10.6). Mitiga robo de refresh tokens.
**Alternativa**: Refresh sin rotation (más simple pero menos seguro).

### D3: Almacenamiento de refresh tokens en BD hasheados
**Decisión**: Se almacena SHA-256 del refresh token, no el token plano.
**Rationale**: Si la BD se filtra, los refresh tokens no pueden reusarse. El token plano solo existe en memoria del cliente y en la respuesta HTTP.
**Alternativa**: Almacenar token plano (más simple, pero vulnerable a filtración de BD).

### D4: Rate limiting en memoria
**Decisión**: Diccionario `{IP:email} → [timestamps]` con ventana deslizante de 60s, máximo 5 intentos.
**Rationale**: No requiere infraestructura externa. Suficiente para etapa temprana. Fácil de reemplazar por Redis cuando sea necesario.
**Alternativa**: Redis (mejor para multi-instancia, pero sobreingeniería ahora).

### D5: 2FA como gate entre validación de credenciales y emisión de sesión
**Decisión**: Login exitoso → si usuario tiene 2FA habilitado → responder con `{requires_2fa: true, session_token: "..."}` (token de sesión temporal) → cliente redirige a verify → verify emite el JWT real.
**Rationale**: No se puede acceder al sistema sin pasar 2FA, pero el usuario no necesita repetir credenciales.
**Alternativa**: Emitir access token con claim `2fa_pending` (complejidad extra en el middleware de verificación).

### D6: `get_current_user` reemplaza a `get_tenant` como dependencia base
**Decisión**: `get_current_user` resuelve user_id, tenant_id y roles desde el JWT. `get_tenant` se convierte en un derivado de `get_current_user` (obtiene `tenant_id` del usuario autenticado).
**Rationale**: La identidad completa viaja en el token. No tiene sentido resolver tenant separadamente.
**Impacto**: C-02 `core/tenancy.py` y `core/dependencies.py` se actualizan.

### D7: Modelo User con tenant_id
**Decisión**: `User` pertenece a un tenant (`tenant_id` FK). Cada tenant tiene sus propios usuarios. El email es único dentro del tenant (no global).
**Rationale**: Es coherente con el diseño multi-tenant desde C-02. Un email puede repetirse entre tenants (usuarios diferentes en distintas instituciones).
**Alternativa**: Email único global (requiere coordinación entre tenants, viola aislamiento).

## Risks / Trade-offs

- **[Rate limit en memoria] → Se pierde al reiniciar la app.** Mitigación: aceptable para early stage. Migrar a Redis en C-12 o cuando sea necesario.
- **[2FA no configurable por tenant] → En C-03 es por usuario.** Mitigación: el modelo lo soporta. La configuración por tenant se puede agregar después sin migración de datos.
- **[Almacenamiento de refresh tokens en BD] → Latencia extra en cada refresh.** Mitigación: mínimo (PK con índice, tabla pequeña). Refresh ocurre cada 15min como máximo.
- **[HS256 → Migración a RS256] → Cambiar la clave requiere que todos los usuarios se reautentiquen.** Mitigación: planificar ventana de migración. Documentado para cuando sea necesario.
