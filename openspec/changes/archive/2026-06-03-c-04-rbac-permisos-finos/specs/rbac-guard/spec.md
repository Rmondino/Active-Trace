## ADDED Requirements

### Requirement: Dependency `require_permission`
El sistema SHALL proveer una FastAPI dependency `require_permission(codigo: str, owner_check: Callable | None = None)` que:
1. Resuelve el usuario actual desde `get_current_user`
2. Obtiene los permisos efectivos del usuario desde `PermissionService`
3. Si el permiso no está en la lista → retorna 403 Forbidden
4. Si el permiso está con alcance `propio` y se provee un `owner_check`, evalúa la función contra el recurso
5. Si `owner_check` retorna `False` → retorna 403 Forbidden

#### Scenario: Usuario con permiso accede al recurso
- **WHEN** un usuario con permiso `calificaciones:importar` intenta acceder a un endpoint protegido con `require_permission("calificaciones:importar")`
- **THEN** el sistema permite el acceso (continúa al handler)

#### Scenario: Usuario sin permiso recibe 403
- **WHEN** un usuario sin permiso `liquidaciones:calcular` intenta acceder a un endpoint protegido con `require_permission("liquidaciones:calcular")`
- **THEN** el sistema retorna 403 Forbidden con detalle "Permiso requerido: liquidaciones:calcular"

#### Scenario: Permiso `propio` sin owner_check falla
- **WHEN** un usuario con permiso `calificaciones:importar` (alcance `propio`) intenta acceder sin proveer `owner_check`
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Permiso `propio` con owner_check exitoso
- **WHEN** un usuario con permiso `calificaciones:importar` (alcance `propio`) intenta acceder a un recurso que le pertenece (owner_check retorna True)
- **THEN** el sistema permite el acceso

#### Scenario: Permiso `propio` con owner_check fallido
- **WHEN** un usuario con permiso `calificaciones:importar` (alcance `propio`) intenta acceder a un recurso que NO le pertenece (owner_check retorna False)
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Permiso `global` ignora owner_check
- **WHEN** un usuario con permiso `usuarios:gestionar` (alcance `global`) intenta acceder incluso si owner_check retornaría False
- **THEN** el sistema permite el acceso (el alcance global sobrepasa el owner_check)

### Requirement: Servicio PermissionService
El sistema SHALL proveer un servicio `PermissionService` con:
- `get_effective_permissions(user_id: str, tenant_id: str) -> list[tuple[str, str]]`: retorna lista de (código_permiso, alcance) para el usuario, unión de todos sus roles
- `has_permission(user_id: str, tenant_id: str, codigo: str) -> bool`: verifica si el usuario tiene el permiso
- `get_permission_scope(user_id: str, tenant_id: str, codigo: str) -> str | None`: retorna el alcance del permiso (`propio` | `global`) o None si no lo tiene

#### Scenario: PermissionService resuelve unión de roles
- **WHEN** se llama a `get_effective_permissions` para un usuario con roles PROFESOR y COORDINADOR
- **THEN** retorna la unión de permisos de ambos roles (incluye `calificaciones:importar` de ambos, sin duplicados)

#### Scenario: PermissionService con usuario sin permisos
- **WHEN** se llama a `get_effective_permissions` para un usuario sin roles
- **THEN** retorna lista vacía

#### Scenario: PermissionService verifica permiso específico
- **WHEN** se llama a `has_permission` para un usuario que tiene el permiso
- **THEN** retorna True

### Requirement: Validación de alcance en owner_check
El guard `require_permission` SHALL aceptar un `owner_check` opcional que es una función asíncrona con firma `(request: Request, user: User) -> bool`.

#### Scenario: Owner_check recibe request y user
- **WHEN** se ejecuta el owner_check
- **THEN** recibe el objeto Request de FastAPI y el User autenticado para extraer IDs de recurso de la request
