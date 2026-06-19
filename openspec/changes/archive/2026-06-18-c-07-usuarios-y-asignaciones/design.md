## Modelo de Datos

### User (expandido — con drop de roles JSONB)

```python
# backend/app/models/user.py
# SE REEMPLAZA el modelo actual

class User(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "user"

    # Existente (se conserva)
    id: Mapped[str]              # UUID PK
    password_hash: Mapped[str]   # Argon2id
    two_fa_secret: Mapped[str | None]
    two_fa_enabled: Mapped[bool] # default False

    # Email: cifrado AES-256-GCM + hash para búsqueda (reemplaza el email texto plano)
    email_hash: Mapped[str]      # SHA-256(LOWER(email)) — UNIQUE(tenant_id, email_hash)
    email: Mapped[str]           # AES-256-GCM cifrado

    # NUEVOS campos de perfil
    nombre: Mapped[str]          # NOT NULL
    apellidos: Mapped[str]       # NOT NULL
    dni: Mapped[str]             # Cifrado AES-256-GCM
    cuil: Mapped[str | None]     # Cifrado
    cbu: Mapped[str | None]      # Cifrado
    alias_cbu: Mapped[str | None] # Cifrado
    banco: Mapped[str | None]
    regional: Mapped[str | None]
    legajo: Mapped[str | None]   # Atributo de negocio, NO credencial
    legajo_profesional: Mapped[str | None]
    facturador: Mapped[bool]     # default False
    estado: Mapped[str]          # "Activo" | "Inactivo", default "Activo"

    # ELIMINADO:
    # roles: Mapped[list]  ← JSONB obsoleto desde C-04 RBAC
```

**Estrategia de cifrado de email**:
- Se agrega `email_hash = SHA-256(LOWER(email))` para login lookup y UNIQUE constraint.
- `email` almacena el valor **cifrado** con AES-256-GCM.
- Al login: se busca por `email_hash`, se descifra `email` para mostrar en perfil.
- Para 2FA provisioning: se descifra el email antes de usarlo como `issuer_name`.

**Estrategia de cifrado de PII**:
- `dni`, `cuil`, `cbu`, `alias_cbu` se cifran con AES-256-GCM (módulo existente `app.core.security`).
- Se descifran al leer para el ADMIN o para el propio usuario.
- En listados (GET /api/admin/usuarios) se devuelven **enmascarados** (ej: `"dni": "*********123"`).

### Asignacion (nuevo — reemplaza funcionalmente el JSONB roles)

```python
# backend/app/models/asignacion.py

class Asignacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "asignacion"

    id: Mapped[str]                   # UUID PK
    usuario_id: Mapped[str]           # FK → User.id (NOT NULL)
    rol: Mapped[str]                  # "PROFESOR" | "TUTOR" | "COORDINADOR" | "NEXO" | "ADMIN" | "FINANZAS"
    materia_id: Mapped[str | None]    # FK → Materia.id
    carrera_id: Mapped[str | None]    # FK → Carrera.id
    cohorte_id: Mapped[str | None]    # FK → Cohorte.id
    comisiones: Mapped[list]          # JSONB, default []
    responsable_id: Mapped[str | None] # FK → User.id (jerarquía)
    desde: Mapped[date]               # Inicio vigencia
    hasta: Mapped[date | None]        # Fin vigencia (None = abierta)

    # relaciones
    usuario: relationship -> User (foreign_keys=[usuario_id])
    materia: relationship -> Materia
    carrera: relationship -> Carrera
    cohorte: relationship -> Cohorte
    responsable: relationship -> User (remote_side=[id], foreign_keys=[responsable_id])
```

## PermissionService refactor (usa Asignacion en vez de user.roles)

El cambio más importante: `PermissionService.get_effective_permissions()` ya NO lee `user.roles` (JSONB). En su lugar:

```python
async def get_effective_permissions(self, user: User) -> list[tuple[str, str]]:
    # 1. Obtener roles activos desde Asignacion (con vigencia)
    result = await self.db.execute(
        select(Asignacion.rol).where(
            Asignacion.usuario_id == user.id,
            Asignacion.tenant_id == user.tenant_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= date.today(),
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= date.today()),
        )
    )
    role_slugs = list(set(row[0].lower() for row in result.all()))
    if not role_slugs:
        return []

    # 2. El resto igual: lookup de Rol → RolPermiso
    result = await self.db.execute(
        select(Rol.id).where(
            Rol.slug.in_(role_slugs),
            Rol.deleted_at.is_(None),
        )
    )
    role_ids = [row[0] for row in result.all()]
    ...
```

**JWT**: `create_token()` ya NO incluye `roles` del JSONB. Se puede:
- Opción A (recomendada): sacar `roles` del JWT. Cada request resuelve permisos desde Asignacion.
- Opción B: resolver roles desde Asignacion al login e incluirlos en el JWT.

Vamos con **Opción A**: el JWT solo lleva `sub` (user_id), `tenant_id`, `exp`. Los permisos se resuelven siempre server-side desde Asignacion.

## Repositorios

### UserRepository

```python
class UserRepository(BaseRepository[User]):
    model_class = User

    async def get_by_email_hash(self, tenant_id: str, email_hash: str) -> User | None
    async def get_by_legajo(self, tenant_id: str, legajo: str) -> User | None
    async def search(self, tenant_id: str, query: str) -> list[User]  # nombre/apellido/legajo
    async def exists_by_email_hash(self, tenant_id: str, email_hash: str, exclude_id: str | None = None) -> bool
```

### AsignacionRepository

```python
class AsignacionRepository(BaseRepository[Asignacion]):
    model_class = Asignacion

    async def get_vigentes(self, tenant_id: str, fecha: date | None = None) -> list[Asignacion]
    async def get_by_usuario(self, tenant_id: str, usuario_id: str, solo_vigentes: bool = True) -> list[Asignacion]
    async def get_by_materia(self, tenant_id: str, materia_id: str, solo_vigentes: bool = True) -> list[Asignacion]
    async def get_by_rol(self, tenant_id: str, rol: str, solo_vigentes: bool = True) -> list[Asignacion]
    async def get_active_role_slugs(self, tenant_id: str, usuario_id: str) -> list[str]  # para PermissionService
```

**Filtro de vigencia**:
```sql
WHERE desde <= :hoy AND (hasta IS NULL OR hasta >= :hoy)
```

## Schemas Pydantic

### `backend/app/schemas/user.py`

```python
class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    apellidos: str
    email: str
    dni: str
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    dni: str | None = None
    # ... resto opcional
    estado: str | None = None

class UserRead(BaseModel):       # Para listados — PII enmascarada
    model_config = ConfigDict(extra="forbid")
    id: str
    nombre: str
    apellidos: str
    email: str                   # Enmascarado: "j***@dominio.com"
    dni: str | None = None       # Enmascarado: "*********123"
    legajo: str | None = None
    regional: str | None = None
    estado: str
    facturador: bool

class UserDetail(BaseModel):     # Para lectura directa (ADMIN) — PII completa
    model_config = ConfigDict(extra="forbid")
    id: str
    nombre: str
    apellidos: str
    email: str                   # Texto plano
    dni: str                     # Texto plano
    cuil: str | None
    cbu: str | None
    alias_cbu: str | None
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: str
```

### `backend/app/schemas/asignacion.py`

```python
class AsignacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: str
    rol: str                     # Enumerado de roles válidos
    materia_id: str | None = None
    carrera_id: str | None = None
    cohorte_id: str | None = None
    comisiones: list[str] = []
    responsable_id: str | None = None
    desde: date
    hasta: date | None = None

class AsignacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rol: str | None = None
    materia_id: str | None = None
    carrera_id: str | None = None
    cohorte_id: str | None = None
    comisiones: list[str] | None = None
    responsable_id: str | None = None
    desde: date | None = None
    hasta: date | None = None

class AsignacionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    usuario_id: str
    rol: str
    materia_id: str | None
    carrera_id: str | None
    cohorte_id: str | None
    comisiones: list[str]
    responsable_id: str | None
    desde: date
    hasta: date | None
    estado_vigencia: str          # "Vigente" | "Vencida" (derivado)
```

## Endpoints

### `/api/admin/usuarios` (require_permission("usuarios:gestionar"))

| Método | Ruta | Request | Response | Notas |
|--------|------|---------|----------|-------|
| `POST` | `/api/admin/usuarios` | `UserCreate` | `UserDetail` | Cifra PII + genera email_hash |
| `GET` | `/api/admin/usuarios` | query: search, estado | `list[UserRead]` | PII enmascarada |
| `GET` | `/api/admin/usuarios/{id}` | — | `UserDetail` | PII completa (ADMIN) |
| `PUT` | `/api/admin/usuarios/{id}` | `UserUpdate` | `UserDetail` | Recifra PII modificada |
| `DELETE` | `/api/admin/usuarios/{id}` | — | 204 | Soft delete |

### `/api/usuarios/me` (require_auth)

| Método | Ruta | Response | Notas |
|--------|------|----------|-------|
| `GET` | `/api/usuarios/me` | `UserDetail` | PII descifrada para el titular |
| `GET` | `/api/usuarios/me/asignaciones` | `list[AsignacionRead]` | Solo vigentes |

### `/api/asignaciones` (require_permission("equipos:asignar"))

| Método | Ruta | Comportamiento |
|--------|------|---------------|
| `POST` | `/api/asignaciones` | Crear asignación |
| `GET` | `/api/asignaciones` | Listar (filtros: usuario_id, materia_id, rol, vigente) |
| `GET` | `/api/asignaciones/{id}` | Detalle |
| `PUT` | `/api/asignaciones/{id}` | Actualizar |
| `DELETE` | `/api/asignaciones/{id}` | Soft delete |

## Migración 005 (data migration — CUIDADO)

```
alembic revision -m "005_enrich_user_add_asignacion"
```

Operaciones en orden:

1. **ALTER TABLE user ADD COLUMN**:
   - `email_hash VARCHAR` nullable inicialmente
   - `nombre VARCHAR` nullable inicialmente
   - `apellidos VARCHAR` nullable inicialmente
   - `dni TEXT`, `cuil TEXT`, `cbu TEXT`, `alias_cbu TEXT` (nullable)
   - `banco VARCHAR`, `regional VARCHAR`
   - `legajo VARCHAR`, `legajo_profesional VARCHAR`
   - `facturador BOOLEAN DEFAULT FALSE`
   - `estado VARCHAR DEFAULT 'Activo'`

2. **Data migration — emails existentes**:
   ```python
   # En la migración (datos), para cada user:
   # 1. Leer email en texto plano
   # 2. email_hash = SHA256(LOWER(email))
   # 3. email_cifrado = AES256_GCM_encrypt(email)
   # 4. UPDATE user SET email_hash=..., email=email_cifrado
   ```

3. **CREATE TABLE asignacion**.

4. **Data migration — roles JSONB a Asignacion**:
   ```python
   # Para cada user con roles != []:
   # Por cada rol en user.roles:
   #   INSERT INTO asignacion (id, usuario_id, tenant_id, rol, desde, ...)
   #   con desde = fecha actual, hasta = NULL
   ```

5. **DROP COLUMN roles** de `user`.

6. **ALTER COLUMN**:
   - `email_hash SET NOT NULL`
   - `nombre SET NOT NULL`, `apellidos SET NOT NULL`
   - `ADD UNIQUE (tenant_id, email_hash)`
   - `CREATE INDEX ON user (tenant_id, LOWER(email_hash))`

## Integración con el flujo de login

`auth_service.authenticate()` cambia:
```python
# ANTES: select(User).where(User.email == email)
# DESPUÉS:
email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
result = await db.execute(
    select(User).where(User.email_hash == email_hash, User.deleted_at.is_(None))
)
```

`auth_service.login()` ya NO incluye `roles` en la respuesta del JWT (se elimina del payload). El JWT solo lleva `sub`, `tenant_id`, `exp`.

## Tests (TDD estricto — governance CRITICAL)

### Safety Net (primero)
- Ejecutar tests existentes, capturar baseline (133 tests pasando)

### RED → GREEN → TRIANGULATE → REFACTOR por cada task

**Modelos**:
- User con campos nuevos, cifrado round-trip, email_hash
- Asignacion con relaciones, comisiones JSONB
- Que `roles` JSONB ya no existe en el modelo

**Repositorios**:
- UserRepository CRUD, búsqueda por email_hash, exists_by_email_hash
- AsignacionRepository CRUD, get_vigentes, get_by_usuario, filtro vigencia
- Multi-tenant isolation

**PermissionService refactor**:
- Que resuelve roles desde Asignacion (con vigencia)
- Que asignación vencida NO otorga permisos
- Que unión de roles funciona (multi-rol)
- Que el JSONB `user.roles` ya no se consulta

**Routers**:
- CRUD endpoints, PII enmascarada en listados, completa en detalle (ADMIN)
- 403 sin permiso, 409 email duplicado
- 404 not found
- `GET /api/usuarios/me` devuelve datos del usuario autenticado

**Login flow**:
- authenticate() funciona con email_hash
- JWT sin roles claim (o roles derivados de Asignacion si se opta por incluirlos)

**Multi-tenant**:
- Usuario creado en tenant A no visible en tenant B
- Asignaciones no se cruzan entre tenants

## Punto 5: User vs Usuario

**Recomendación**: mantener `User`. Razones:
- El rename tocaría 15+ archivos (models, services, routers, tests, JWT, auth flow)
- El código existente está todo en inglés
- La tabla `user` en SQL es palabra reservada pero funciona
- La KB puede llamarlo Usuario; el nombre del modelo SQLAlchemy es un detalle técnico

**Si se decide renombrar**: sería un change separado (refactor puro, sin cambio funcional) para no mezclar con la lógica de C-07.
