## Why

El sistema necesita representar a las personas que interactúan con él (docentes, alumnos, administradores) con sus datos reales: nombre, DNI, CUIL, CBU, datos bancarios — todos **sensibles y obligados a cifrado en reposo**. El modelo `User` actual (creado en C-03) solo tiene email, password_hash y 2FA; es una identidad de login, no un perfil de persona.

Además, hace falta el modelo de **Asignación** que vincula a un usuario con un rol y un contexto académico (materia, carrera, cohorte), con vigencia temporal. Sin esto, no se puede determinar qué permisos tiene un usuario sobre qué recursos, ni gestionar equipos docentes.

## What Changes

### Modelo Usuario enriquecido
- El modelo `User` existente se expande con campos de perfil: `nombre`, `apellidos`, `dni`, `cuil`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `estado`.
- Los campos `[cifrado]` (email, dni, cuil, cbu, alias_cbu) se almacenan con AES-256-GCM usando el módulo existente `app.core.security`.
- Se agrega el permiso `usuarios:gestionar` para ABM de usuarios (ADMIN).

### Modelo Asignacion (nuevo)
- Entidad `Asignacion` que vincula `Usuario` ↔ `Rol` ↔ contexto académico (`Materia`, `Carrera`, `Cohorte`).
- Vigencia temporal (`desde`, `hasta`) que determina si la asignación está activa.
- `responsable_id` para jerarquía (quién supervisa al asignado).
- `comisiones` como lista de textos para comisiones específicas.

### Endpoints
- `POST/GET/PUT /api/admin/usuarios` — CRUD de usuarios (guard `usuarios:gestionar`, ADMIN)
- `POST/GET/PUT/DELETE /api/asignaciones` — CRUD de asignaciones (guard `equipos:asignar`, COORDINADOR/ADMIN)
- `GET /api/usuarios/me` — perfil propio del usuario autenticado (PROFESOR, TUTOR, etc.)
- `GET /api/usuarios/{id}/asignaciones` — asignaciones de un usuario (con permiso)

### Reglas de negocio
- Unicidad `(tenant_id, email)` en Usuario.
- PII cifrada nunca expuesta en logs ni en respuestas (excepto para el propio usuario o ADMIN).
- Asignación vencida no otorga permisos pero se conserva como histórico.
- `estado_vigencia` es derivado (no almacenado): se calcula comparando fechas contra la fecha actual.
- Un usuario puede tener múltiples asignaciones activas simultáneas (multi-rol, multi-materia).

### Migración
- `Migración 005`: alter table `user` + creación de tabla `asignacion`.

## Capabilities

### New Capabilities
- `user-admin`: CRUD de usuarios del tenant con PII cifrada, búsqueda por email/legajo/nombre, activación/desactivación.
- `asignacion-crud`: CRUD de asignaciones usuario↔rol↔contexto, validación de vigencia, filtros por materia/carrera/cohorte/rol.
- `user-profile`: Perfil propio del usuario autenticado, acceso a sus asignaciones activas.

### Modified Capabilities
- *(Ninguna — los specs existentes de auth y RBAC no cambian su comportamiento)*

## Impact

- **Modelos**: `backend/app/models/user.py` se expande (~50 → ~120 LOC). Nuevo `backend/app/models/asignacion.py`.
- **Repositorios**: Nuevos `UserRepository` y `AsignacionRepository` con tenant scope + filtros de vigencia.
- **Routers**: Nuevos `backend/app/routers/admin/usuarios.py` y `backend/app/routers/asignaciones.py`.
- **Auth**: El guard `require_permission` debe considerar la vigencia de asignaciones (el `PermissionService` existente ya resuelve permisos efectivos, hay que integrar el filtro de vigencia).
- **Datos**: La migración 005 debe manejar datos existentes en `user` (agregar columnas con defaults para registros previos).
- **Tests**: Suite completa con PII cifrada, vigencia, multi-tenant, multi-rol, jerarquía responsable.
