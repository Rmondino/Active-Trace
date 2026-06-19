## Context

C-03 estableció la autenticación: cualquier usuario con JWT válido puede acceder a endpoints protegidos por `get_current_user`. Sin embargo, no hay granularidad de permisos — un ALUMNO podría llamar a endpoints de liquidaciones. C-04 implementa el middleware de autorización faltante.

Actualmente `User.roles` es un JSONB list (legacy de C-03) que se incluye en el JWT. C-04 formalizará esto: el JSONB se mantiene como cache del frontend, pero los permisos efectivos se resuelven siempre server-side contra las tablas de RBAC.

## Goals / Non-Goals

**Goals:**
- Catálogo administrable de roles (CRUD), permisos (`modulo:accion`) y la matriz rol→permiso como datos en DB
- Seed automático de los 7 roles del dominio con su matriz de permisos base (KB §3.3)
- Servicio `PermissionService` que resuelve permisos efectivos: unión de permisos de todos los roles del usuario, acotados por tenant
- Guard FastAPI `require_permission("modulo:accion")` que intercepta antes del handler y retorna 403 si falta el permiso
- Soporte para alcance `(propio)` vs global: el guard puede recibir una función lambda que evalúa ownership del recurso

**Non-Goals:**
- Proteger endpoints existentes con `require_permission` — eso ocurre en los changes de cada módulo (C-05+)
- Vigencia temporal de asignaciones (se implementa en C-07 con la tabla Asignacion)
- Impersonación (C-05 audit-log)
- UI de administración de roles (C-21+)

## Decisions

### D1 — Roles como tabla separada (no solo JSONB)
- **Decisión**: Crear tabla `rol` normalizada en lugar de depender solo del JSONB `User.roles`
- **Opción A** (elegida): Tabla `rol` + tabla `permiso` + tabla `rol_permiso`. Los roles del usuario se almacenan como FK en una tabla `usuario_rol` (o se mantiene JSONB `User.roles` como cache + se normaliza).
- **Opción B**: Mantener todo en JSONB. Rechazado porque imposibilita queries de "quiénes tienen permiso X" y auditoría.
- **Conclusión**: Usar modelo relacional. El JSONB `User.roles` se mantiene como cache para el frontend (evita join en cada request), pero `PermissionService` siempre resuelve desde las tablas normalizadas.

### D2 — Resolución de permisos server-side, no en JWT
- **Decisión**: El JWT solo lleva `roles` (nombres), no la lista de permisos. Cada request resuelve permisos contra DB.
- **Racional**: Los permisos pueden cambiar (un ADMIN puede ajustar la matriz) sin invalidar sesiones activas. La resolución es una query simple indexada (rol_permiso por rol_id).
- **Caché opcional futura**: Redis (C-XX) si la latencia se vuelve problema.

### D3 — `require_permission` como dependencia parametrizable
- **Decisión**: `require_permission("modulo:accion")` retorna una dependencia FastAPI. Variante contextual: `require_permission("modulo:accion", resource_owner_getter=...)` para validar alcance `(propio)`.
- **Uso típico**:
  ```python
  @router.get("/entregas/{id}")
  async def get_entrega(
      _: None = Depends(require_permission("entregas:ver")),
      ...
  ):
  ```
- Para alcance `(propio)`:
  ```python
  async def _es_su_entrega(request, entrega_id, user) -> bool:
      entrega = await entrega_repo.get(entrega_id)
      return entrega and entrega.alumno_id == user.id

  @router.get("/entregas/{id}")
  async def get_entrega(
      _: None = Depends(require_permission("entregas:ver", owner_check=_es_su_entrega)),
      ...
  ):
  ```

### D4 — Seed versionado, no hardcode
- **Decisión**: La matriz de permisos base (KB §3.3) se siembra con datos en la migración Alembic 003, no en código Python.
- **Racional**: Al ser datos, cualquier tenant puede customizar su matriz post-seed sin modificar código. La migración es idempotente (INSERT ... ON CONFLICT DO NOTHING).

### D5 — Alcance `(propio)` vs global como columna en RolPermiso
- **Decisión**: Agregar columna `alcance` (ENUM: `propio` | `global`) en `rol_permiso`.
- **Significado**: `propio` significa que el permiso solo aplica sobre recursos del propio usuario (e.g., un PROFESOR ve SOLO sus comisiones). `global` aplica sin restricción de ownership.
- **Validación**: El guard `require_permission` con `owner_check` evalúa dinámicamente; si el permiso es `global`, ignora el `owner_check`.

## Risks / Trade-offs

- [Riesgo] DB query por request para resolver permisos puede sumar latencia. → Mitigación: query simple indexada (<5ms); caché Redis post-MVP.
- [Riesgo] El seed de la matriz puede quedar desactualizado vs la KB. → Mitigación: esta propuesta es la referencia; al cambiar la KB, debe actualizarse el seed en una migración.
- [Trade-off] Mantener JSONB User.roles como cache duplica datos. → Aceptado por beneficio UX (frontend no necesita llamar a /me/permissions constantemente).

## Open Questions

- ¿El seed se ejecuta automáticamente en `alembic upgrade head` o debe ser un comando separado? → Se ejecuta en la migración 003 (idempotente).
- ¿`alcance` en `rol_permiso` debe ser extensible a más valores (e.g., `cohorte`, `carrera`)? → Por ahora solo `propio` | `global`; se extiende si surge necesidad.
