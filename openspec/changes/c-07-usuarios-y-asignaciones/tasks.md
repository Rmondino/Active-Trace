## 1. Modelo User expandido + Asignacion

- [x] 1.1 Expandir `backend/app/models/user.py`: agregar campos de perfil (nombre, apellidos, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, facturador, estado), reemplazar `email` por `email` cifrado + `email_hash`, eliminar `roles` JSONB
- [x] 1.2 Crear `backend/app/models/asignacion.py` con Asignacion (usuario_id, rol, materia_id, carrera_id, cohorte_id, comisiones JSONB, responsable_id, desde, hasta, soft delete, tenant scope)
- [x] 1.3 Registrar Asignacion en `backend/app/models/__init__.py`

## 2. Repositorios

- [x] 2.1 Crear `backend/app/repositories/user_repository.py` con UserRepository (get_by_email_hash, get_by_legajo, search, exists_by_email_hash)
- [x] 2.2 Crear `backend/app/repositories/asignacion_repository.py` con AsignacionRepository (get_vigentes, get_by_usuario, get_by_materia, get_by_rol, get_active_role_slugs)
- [x] 2.3 Registrar repositorios en `backend/app/repositories/__init__.py`

## 3. Schemas Pydantic

- [x] 3.1 Crear `backend/app/schemas/user.py` con UserCreate, UserUpdate, UserRead (PII enmascarada), UserDetail (PII completa), todos con extra='forbid'
- [x] 3.2 Crear `backend/app/schemas/asignacion.py` con AsignacionCreate, AsignacionUpdate, AsignacionRead (con estado_vigencia derivado), todos con extra='forbid'
- [x] 3.3 Registrar schemas en `backend/app/schemas/__init__.py`

## 4. Routers

- [x] 4.1 Crear `backend/app/routers/admin/usuarios.py` con CRUD de usuarios (POST/GET/GET id/PUT/DELETE, require_permission("usuarios:gestionar"), PII enmascarada en listados, cifrado automático)
- [x] 4.2 Crear `backend/app/routers/asignaciones.py` con CRUD de asignaciones (POST/GET/GET id/PUT/DELETE, require_permission("equipos:asignar"))
- [x] 4.3 Crear `backend/app/routers/usuarios_me.py` con GET /api/usuarios/me y GET /api/usuarios/me/asignaciones
- [x] 4.4 Registrar routers en `backend/app/main.py`

## 5. Migración 005 (data migration)

- [x] 5.1 Generar migración 005 con ALTER TABLE user (nuevas columnas), CREATE TABLE asignacion, DROP COLUMN roles
- [x] 5.2 Agregar data migration: cifrar emails existentes, calcular email_hash, migrar roles JSONB → asignaciones
- [x] 5.3 Ejecutar alembic upgrade head y verificar tablas + datos migrados
- [x] 5.4 Seed del permiso `usuarios:gestionar` para rol ADMIN en la migración (ya existe desde 003_create_rbac_tables)

## 6. Refactor PermissionService y auth flow

- [x] 6.1 Refactorizar `PermissionService.get_effective_permissions()` para leer roles desde Asignacion (con vigencia) en vez de user.roles JSONB
- [x] 6.2 Actualizar `auth_service.authenticate()` para buscar por email_hash
- [x] 6.3 Actualizar JWT `create_token()`: remover roles del payload (solo sub + tenant_id + exp)
- [x] 6.4 Agregar helper `mask_pii()` para enmascarar datos sensibles en respuestas de listado

## 7. Tests (TDD estricto)

- [x] 7.1 Safety Net: ejecutar tests existentes, capturar baseline (133 tests pasando)
- [x] 7.2 Tests de modelo: User expandido con cifrado round-trip, email_hash, Asignacion con relaciones, que roles JSONB no existe
- [x] 7.3 Tests de repositorio: UserRepository CRUD + exists_by_email_hash + search, AsignacionRepository CRUD + get_vigentes + get_by_usuario + filtro vigencia
- [x] 7.4 Tests de PermissionService refactor: roles desde Asignacion, vencida no otorga, multi-rol union
- [x] 7.5 Tests de router usuarios: CRUD, PII enmascarada, 403, 409 email duplicado, 404, soft delete
- [x] 7.6 Tests de router asignaciones: CRUD, vigencia, estado_vigencia derivado, filtros
- [x] 7.7 Tests de perfil propio: GET /api/usuarios/me, GET /api/usuarios/me/asignaciones
- [x] 7.8 Tests de multi-tenant isolation: usuarios/asignaciones no visibles entre tenants
- [x] 7.9 Tests de login con email_hash: authenticate funciona (test_auth.TestLogin), JWT sin roles (test_auth.TestJWT.test_create_and_verify_access_token line 104)
- [x] 7.10 Verificar cobertura ≥80% líneas (80%) y ≥90% reglas de negocio (PII, vigencia, multi-tenant, permisos cubiertos)
