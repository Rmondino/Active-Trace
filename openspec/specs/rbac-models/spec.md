# RBAC — Modelos de Roles y Permisos

## ADDED Requirements

### Requirement: Catálogo de roles administrable
El sistema SHALL mantener un catálogo de roles (tabla `rol`) donde cada rol tenga: slug (identificador único URL-safe, e.g. "profesor"), nombre descriptivo (e.g. "Profesor"), y descripción opcional.

El catálogo SHALL ser administrable por usuarios con permiso `rbac:gestionar` (ADMIN del tenant), permitiendo crear, editar y desactivar roles.

#### Scenario: Crear nuevo rol
- **WHEN** un ADMIN ejecuta `POST /api/roles` con slug, nombre y descripción
- **THEN** el sistema crea el rol y lo persiste en la tabla `rol`

#### Scenario: Slug duplicado es rechazado
- **WHEN** un ADMIN intenta crear un rol con un slug que ya existe
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Roles del dominio no se pueden eliminar (solo desactivar)
- **WHEN** un ADMIN intenta eliminar un rol del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS)
- **THEN** el sistema retorna 400 con mensaje "No se puede eliminar un rol del dominio"

### Requirement: Catálogo de permisos administrable
El sistema SHALL mantener un catálogo de permisos (tabla `permiso`) donde cada permiso tenga: código (`modulo:accion`, e.g. "calificaciones:importar") y descripción.

El catálogo SHALL ser extensible: nuevos permisos se agregan mediante migraciones o desde el panel de administración.

#### Scenario: Consultar catálogo de permisos
- **WHEN** un ADMIN consulta `GET /api/permisos`
- **THEN** el sistema retorna la lista completa de permisos disponibles en el tenant

#### Scenario: Código de permiso duplicado es rechazado
- **WHEN** se intenta crear un permiso con un código `modulo:accion` que ya existe
- **THEN** el sistema retorna 409 Conflict

### Requirement: Matriz Rol→Permiso
El sistema SHALL mantener una tabla `rol_permiso` que asigna permisos a roles, con los siguientes atributos:
- `rol_id`: FK al rol
- `permiso_id`: FK al permiso
- `alcance`: ENUM con valores `propio` | `global`

Donde `propio` significa que el permiso solo aplica sobre recursos del propio usuario, y `global` aplica sin restricción de ownership.

#### Scenario: Asignar permiso a rol
- **WHEN** un ADMIN asigna un permiso a un rol con alcance `global`
- **THEN** el sistema crea el registro en `rol_permiso`

#### Scenario: Consultar permisos de un rol
- **WHEN** se consultan los permisos de un rol
- **THEN** el sistema retorna la lista de permisos con su alcance

### Requirement: Resolución de permisos efectivos del usuario
El sistema SHALL proveer un servicio que, dado un usuario, retorne la unión de todos los permisos de todos sus roles, acotados por tenant.

#### Scenario: Usuario con múltiples roles
- **WHEN** un usuario tiene roles PROFESOR y COORDINADOR
- **THEN** sus permisos efectivos son la unión de los permisos de ambos roles

#### Scenario: Usuario sin roles
- **WHEN** un usuario no tiene roles asignados
- **THEN** sus permisos efectivos son un conjunto vacío
