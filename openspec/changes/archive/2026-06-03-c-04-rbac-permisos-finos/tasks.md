## 1. Modelos RBAC y migración

- [x] 1.1 Crear `models/rol.py` con Rol (id UUID, slug único, nombre, descripción nullable, timestamps, soft delete)
- [x] 1.2 Crear `models/permiso.py` con Permiso (id UUID, codigo único `modulo:accion`, descripción, timestamps)
- [x] 1.3 Crear `models/rol_permiso.py` con RolPermiso (id UUID, rol_id FK, permiso_id FK, alcance ENUM `propio`|`global`, unique constraint rol_id+permiso_id)
- [x] 1.4 Generar migración Alembic 003 con las tres tablas
- [x] 1.5 Agregar seed de roles del dominio (7 roles: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) en la migración
- [x] 1.6 Agregar seed de permisos base (22 códigos `modulo:accion`) en la migración
- [x] 1.7 Agregar seed de matriz rol→permiso (KB §3.3) en la migración con alcance `propio`|`global`
- [x] 1.8 Ejecutar `alembic upgrade head` y verificar tablas + datos seed

## 2. PermissionService

- [x] 2.1 Implementar `PermissionService` con `get_effective_permissions(user) -> list[tuple[str, str]]`
- [x] 2.2 Implementar `has_permission(user, codigo) -> bool`
- [x] 2.3 Implementar `get_permission_scope(user, codigo) -> str | None`
- [x] 2.4 Resolver unión de permisos de todos los roles del usuario (sin duplicados)
- [x] 2.5 Asegurar scope por tenant (los permisos de un tenant A no afectan al tenant B)

## 3. Guard `require_permission`

- [x] 3.1 Implementar `require_permission(codigo: str, owner_check: Callable | None = None)` como factory de dependencias FastAPI
- [x] 3.2 Integrar con `get_current_user` para obtener el usuario autenticado
- [x] 3.3 Implementar lógica: sin permiso → 403; permiso `propio` sin owner_check → 403; owner_check False → 403
- [x] 3.4 Exportar `require_permission` desde `core/dependencies.py`
- [x] 3.5 Test helpers creados (`_create_user`, `_create_tenant`, `_seed_role_permiso`, `_build_test_app`)

## 4. Tests

- [x] 4.1 Tests de modelos: crear rol, permiso, rol_permiso con alcance, unique constraint
- [x] 4.2 Tests de seed: slug único, default is_domain_role
- [x] 4.3 Tests de PermissionService: permisos efectivos (unión), usuario sin roles, has/scope, deduplicación
- [x] 4.4 Tests de require_permission: usuario con permiso → OK, sin permiso → 403
- [x] 4.5 Tests de alcance `propio`: con owner_check OK, con owner_check False, sin owner_check
- [x] 4.6 Tests de alcance `global`: sobrepasa owner_check
- [x] 4.7 Tests de aislamiento multi-tenant: permisos no heredados entre tenants
- [x] 4.8 Suite completa 80/80 pruebas verdes
