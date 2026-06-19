## Context

C-01 foundation-setup creó el esqueleto del backend: FastAPI con health-check, engine async SQLAlchemy, logging JSON, OTel, y slots reservados en `core/` para los módulos transversales. El modelo `Base` declarativo existe pero está vacío (sin mixins, sin tenant scope). El slot `core/security.py` es un placeholder y `core/tenancy.py` también.

C-02 es el **cimiento de datos**: materializa el modelo multi-tenant desde la base. Es governance CRÍTICO porque todo el modelo de autorización, aislamiento y seguridad depende de estas decisiones. Ningún módulo de dominio (usuarios, materias, calificaciones) puede construirse sin esto.

## Goals / Non-Goals

**Goals:**

1. **Modelo `Tenant`**: tabla raíz con `id`, `slug` (único), `nombre`, `config` (JSONB), `estado`.
2. **Mixins ORM base**:
   - `TimeStampedMixin`: `created_at`, `updated_at` con valores automáticos.
   - `SoftDeleteMixin`: `deleted_at` nullable; soft delete en queries por defecto.
   - `TenantScopedMixin`: `tenant_id` FK → Tenant; filtro automático en queries.
3. **`Base` declarativa** que combina los tres mixins + `id` UUID PK. Todas las tablas de dominio heredarán de esta `Base`.
4. **`BaseRepository[ModelT]`** genérico con:
   - `get(id)`: obtiene por ID + tenant scope. Soft-delete aware (no retorna borrados).
   - `list(filters)`: lista con filtros + tenant scope. Sin borrados. Paginación offset/limit.
   - `create(data)`: crea con tenant_id automático desde el contexto.
   - `update(id, data)`: actualiza con scope.
   - `soft_delete(id)`: marca deleted_at, no hard delete.
   - `restore(id)`: recupera un soft-delete.
   - `list_all()`: explícitamente salta tenant scope (uso controlado: seeders, migraciones).
5. **Utilidad AES-256**: cifrar/descifrar strings usando `cryptography` library. Clave desde `Settings.ENCRYPTION_KEY`. Función `encrypt(plaintext: str) -> str` y `decrypt(ciphertext: str) -> str`.
6. **Migración Alembic 001**: creación de la tabla `tenant`.
7. **Tests**: aislamiento multi-tenant, soft delete, cifrado round-trip, timestamps automáticos.

**Non-Goals:**

- Auth, JWT, Argon2id (→ C-03).
- Modelos de dominio específicos (Usuario, Carrera, Materia — changes posteriores).
- RBAC, matriz de permisos (→ C-04).
- Audit log (→ C-05).
- Frontend, endpoints HTTP (excepto `/health` que ya existe).

## Decisions

### D1 — Estrategia de mixins ORM

Se usan **mixins de SQLAlchemy** (clases independientes combinadas en `Base`), no herencia única ni composición con eventos. Cada mixin es una clase que declara columnas y hooks de ciclo de vida (`@validates`, `@hybrid_property`, etc.).

```
Base = declarative_base(cls=TimeStampedMixin + SoftDeleteMixin + TenantScopedMixin)
```

Esto permite que las tablas del dominio hereden de `Base` y obtengan todas las columnas y comportamiento transversal sin repetir código.

**Alternativa descartada**: usar `__abstract__` con herencia simple. Se descarta porque no escala a N combinaciones de mixins (algunas tablas podrían no necesitar soft delete, etc.).

### D2 — Filtro automático de tenant en el repositorio

El `BaseRepository` recibe el `tenant_id` en el constructor (resuelto desde la request) y lo aplica como filtro automático en todos los métodos de lectura/escritura. El método `list_all()` es la única excepción y requiere invocación explícita.

```python
class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def get(self, id: UUID) -> ModelT | None:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.tenant_id == self.tenant_id,
            self.model.deleted_at.is_(None),
        )
        ...
```

**Alternativa descartada**: usar SQLAlchemy `viewonly=True` o event listeners para filtrar automáticamente. Se descarta porque el filtro implícito es menos legible que el explícito en el repositorio. Además, los event listeners complican el testing.

### D3 — Soft delete con nullable deleted_at

El soft delete usa una columna `deleted_at: DateTime | None`. Cuando es `NULL`, el registro está activo. Cuando tiene timestamp, está eliminado. Todos los métodos del repositorio filtran `deleted_at.is_(None)` por defecto.

- `soft_delete(id)`: setea `deleted_at = utcnow()`.
- `restore(id)`: setea `deleted_at = None`.
- `get()` y `list()` excluyen borrados.
- El hard delete no existe a nivel de repositorio (solo cascade de DB o migraciones).

### D4 — AES-256 con cryptography library

Se usa la librería `cryptography` (ya en `pyproject.toml`). Algoritmo: AES-256 en modo GCM (autenticado). El output se codifica en base64 para almacenamiento texto.

```
ciphertext = encrypt(plaintext: str, key: bytes) -> str (base64)
plaintext = decrypt(ciphertext: str, key: bytes) -> str
```

- La clave se deriva de `Settings.ENCRYPTION_KEY` (exactamente 32 bytes).
- Cada cifrado genera un nonce aleatorio (12 bytes para GCM).
- El formato del output es `base64(nonce + ciphertext + tag)`.

**Alternativa descartada**: AES-256-CBC. Se descarta porque GCM provee autenticación integrada (no requiere HMAC separado) y es el estándar moderno.

### D5 — Tenant como entidad con slug único

La tabla `Tenant` tiene:
- `id`: UUID PK.
- `slug`: string único, identificador URL-safe (ej: "universidad-nacional").
- `nombre`: string legible.
- `config`: JSONB con configuración específica del tenant.
- `estado`: enum Activo/Inactivo.
- Además hereda de `Base` (timestamps). Pero no tiene `tenant_id` (es la raíz).

### D6 — Estrategia de migración única

La migración 001 crea la tabla `tenant`. No se crean tablas de dominio en C-02 porque no hay modelos de dominio aún. La migración usa el engine async configurado en C-01.

## Risks / Trade-offs

- **[Repository genérico puede ser demasiado rígido para queries complejos]** → Mitigación: el `BaseRepository` cubre el 80% de los casos (CRUD simple). Para queries específicos, los repositorios de dominio extienden `BaseRepository` y agregan métodos custom con filtros adicionales.
- **[AES-256 GCM requiere nonce único por cifrado]** → Mitigación: el nonce se genera con `os.urandom(12)` que es criptográficamente seguro. El riesgo de colisión es negligible.
- **[Soft delete puede acumular datos huérfanos]** → Trade-off aceptado: la auditoría requiere conservar el histórico. Si el volumen crece, se agrega archivado por período (fuera de MVP).
- **[Tenant scope en repositorio puede ser evadido por error]** → Mitigación: el `list_all()` requiere invocación explícita y debe usarse solo en seeders/admin. Code review detecta su uso inapropiado.
- **[Mixins SQLAlchemy pueden tener conflictos de columnas]** → Mitigación: los nombres de columna están prefijados y documentados. Tests de herencia verifican que los mixins sean compatibles.

## Migration Plan

1. Ejecutar `alembic upgrade head` → crea tabla `tenant`.
2. Seed de tenant inicial (manual o script).
3. Tests: correr suite completa y verificar verde.
4. Rollback: `alembic downgrade -1` elimina la tabla `tenant`.

No hay datos de producción en riesgo (primer cambio de modelo).

## Open Questions

- **Seed de tenant inicial**: definir si se crea mediante migración (data migration) o mediante script separado. Decisión: script separado `scripts/seed_tenant.py` para mantener las migraciones libres de datos de seed.
- **Índices adicionales**: definir índices para `tenant.slug` (único), y composite `(tenant_id, deleted_at)` en tablas de dominio. Se definen en migraciones futuras según patrones de query.
