## Why

C-03 implementó la autenticación (quién eres), pero el sistema aún no tiene autorización (qué puedes hacer). Sin un sistema de permisos finos, cualquier usuario autenticado puede acceder a cualquier endpoint — esto es un agujero de seguridad. C-04 implementa el modelo RBAC completo: roles, permisos `modulo:accion`, la matriz rol×permiso como datos administrables, y el guard `require_permission` que protege cada endpoint.

## What Changes

- Modelos `Rol` (catálogo de roles), `Permiso` (catálogo de permisos `modulo:accion`), `RolPermiso` (matriz asignación rol→permiso) — todo como datos, NO hardcodeado
- Seed de los 7 roles del dominio: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
- Seed de la matriz de permisos base según `knowledge-base/03_actores_y_roles.md` §3.3
- Dependencia/guard `require_permission("modulo:accion")` para proteger endpoints
- Servicio `PermissionService` que resuelve permisos efectivos server-side por request (unión de roles del usuario, acotado por tenant)
- Conciencia de `(propio)` vs global: el guard debe poder recibir contexto del recurso para validar ownership
- Migración 003: tablas `rol`, `permiso`, `rol_permiso` + seed data
- El JWT ya incluye `roles` (desde C-03), pero los permisos se resuelven server-side (no viajan en el token)

## Capabilities

### New Capabilities
- `rbac-models`: Modelos Rol, Permiso, RolPermiso con catálogo administrable como datos
- `rbac-seed`: Seed de roles del dominio + matriz de permisos base (KB §3.3)
- `rbac-guard`: Dependency `require_permission("modulo:accion")` para proteger endpoints

### Modified Capabilities
- *(ninguna — C-04 introduce capabilities nuevas, no modifica existentes)*

## Impact

- **Nuevos modelos**: `Rol` (slug, nombre, descripción), `Permiso` (codigo `modulo:accion`, descripción), `RolPermiso` (rol_id, permiso_id, alcance: propio|global)
- **Migración**: 003_create_rbac_tables + seed de datos
- **Nuevo servicio**: `services/permission_service.py` con resolución de permisos y helper de contexto `(propio)`
- **Nueva dependencia**: `require_permission` como FastAPI dependency que reemplazará el chequeo manual de roles
- **Seed data**: ~50 registros en rol_permiso (matriz completa)
- **Endpoints modificados**: ningún endpoint existente se protege aún con `require_permission` — C-04 solo implementa el mecanismo; la protección de cada endpoint se hará en los changes que tocan cada módulo (C-05+)
