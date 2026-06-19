## Modelo de Datos

### VersionPadron

```python
class VersionPadron(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "version_padron"

    id: Mapped[str]              # UUID PK
    materia_id: Mapped[str]      # FK → Materia.id
    cohorte_id: Mapped[str]      # FK → Cohorte.id
    cargado_por: Mapped[str]     # FK → User.id
    cargado_at: Mapped[datetime] # default now()
    activa: Mapped[bool]         # default True — solo una activa por (materia, cohorte)
    origen: Mapped[str]          # "manual" | "moodle"
    total_filas: Mapped[int]     # cantidad de entradas en esta versión
```

**Unicidad**: Una sola versión `activa=True` por `(tenant_id, materia_id, cohorte_id)`. Se garantiza a nivel aplicación: al activar una nueva, se desactivan las anteriores.

### EntradaPadron

```python
class EntradaPadron(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "entrada_padron"

    id: Mapped[str]              # UUID PK
    version_id: Mapped[str]      # FK → VersionPadron.id
    usuario_id: Mapped[str | None]  # FK → User.id (nullable: alumno sin cuenta)
    nombre: Mapped[str]          # desnormalizado para histórico
    apellidos: Mapped[str]
    email: Mapped[str]           # cifrado AES-256-GCM
    comision: Mapped[str | None]
    regional: Mapped[str | None]
```

**Regla**: `usuario_id` puede ser nulo — permite importar alumnos que todavía no tienen cuenta en el sistema. Cuando se cree la cuenta, se puede vincular posteriormente (fuera de este change).

## Repositorios

### VersionPadronRepository

```python
class VersionPadronRepository(BaseRepository[VersionPadron]):
    model_class = VersionPadron

    async def get_activa(self, materia_id: str, cohorte_id: str) -> VersionPadron | None
    async def desactivar_anteriores(self, materia_id: str, cohorte_id: str, except_id: str | None = None) -> None
    async def list_by_materia(self, materia_id: str) -> list[VersionPadron]
    async def vaciar_materia(self, materia_id: str) -> None  # soft delete todas las versiones
```

### EntradaPadronRepository

```python
class EntradaPadronRepository(BaseRepository[EntradaPadron]):
    model_class = EntradaPadron

    async def get_by_version(self, version_id: str) -> list[EntradaPadron]
    async def bulk_create(self, entradas: list[EntradaPadron]) -> None
    async def count_by_version(self, version_id: str) -> int
```

## Flujo de Importación Manual

### Paso 1: Upload + Preview
```
POST /api/padron/import
  Content-Type: multipart/form-data
  Body: file (xlsx/csv), materia_id, cohorte_id
  → Response 200: preview_id, filas_detectadas, columnas, muestra (primeras 5 filas)
```

El archivo se parsea con `openpyxl` (xlsx) o `csv` (csv). Columnas esperadas:
- `nombre`, `apellido(s)`, `email`, `comisión`, `regional`

**Preview**: se almacena temporalmente en memoria (no en DB). Se devuelve:
```json
{
  "preview_id": "uuid",
  "total_filas": 150,
  "columnas": ["nombre", "apellidos", "email", "comision", "regional"],
  "muestra": [
    {"nombre": "Juan", "apellidos": "Pérez", "email": "j...", ...},
    ...
  ],
  "errores": []  // filas con datos inválidos
}
```

### Paso 2: Confirmar
```
POST /api/padron/preview/{preview_id}/confirm
  → Response 201: { version_id, filas_importadas }
```

En este paso:
1. Se crea `VersionPadron` con `activa=False`
2. Se crean `EntradaPadron` para cada fila (bulk insert)
3. Se desactivan versiones anteriores de la misma `(materia, cohorte)`
4. Se marca la nueva versión como `activa=True`
5. Se registra auditoría `PADRON_CARGAR`

### Paso 3 (alternativo): Upload directo sin preview
```
POST /api/padron/import?confirm=true
  → Response 201: { version_id, filas_importadas }
```
Para clients que no necesitan preview (ej: sync automática).

## Moodle Web Services Integration

### Cliente: `integrations/moodle_ws.py`

```python
class MoodleWSClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.retries = 3

    async def get_course_participants(self, course_id: int) -> list[dict]:
        """Obtiene lista de participantes de un curso Moodle.
        Usa core_enrol_get_enrolled_users o gradereport_user_get_gradebook.
        """
        ...

    async def get_course_activities(self, course_id: int) -> list[dict]:
        """Obtiene actividades de un curso Moodle.
        Usa core_course_get_contents.
        """
        ...

    async def get_grades(self, course_id: int, user_ids: list[int]) -> list[dict]:
        """Obtiene calificaciones de usuarios en un curso."""
        ...
```

**Manejo de errores**:
- Timeout: reintenta hasta 3 veces con backoff exponencial.
- Error de conexión: retorna `MoodleWSError` que el router mapea a 502.
- Token inválido: retorna `MoodleWSAuthError` que mapea a 502 con mensaje claro.
- Moodle offline: retorna `MoodleWSUnavailableError`.

### Rutas de Moodle Sync

```
GET /api/padron/moodle/sync?materia_id=X&cohorte_id=Y&course_id=Z
  → Dispara sync on-demand desde Moodle
  → 200: { version_id, filas_sincronizadas, curso, materia }

POST /api/padron/moodle/sync/nocturna
  → Dispara sync programada (también invocable on-demand por ADMIN)
  → Procesa todas las materias con integración Moodle configurada
```

La sync nocturna se programa como tarea del worker (celery o asyncio) con un schedule diario.

## Endpoints Resumen

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `POST` | `/api/padron/import` | `calificaciones:importar` | Upload archivo, opcional `?confirm=true` |
| `GET` | `/api/padron/preview/{preview_id}` | `calificaciones:importar` | Ver preview guardada |
| `POST` | `/api/padron/preview/{preview_id}/confirm` | `calificaciones:importar` | Confirmar import y activar versión |
| `GET` | `/api/padron/versiones?materia_id=X&cohorte_id=Y` | `calificaciones:importar` | Listar versiones de una materia |
| `GET` | `/api/padron/versiones/{version_id}` | `calificaciones:importar` | Detalle de versión (sin PII de alumnos) |
| `DELETE` | `/api/padron/materia/{materia_id}` | `calificaciones:importar` | Vaciar datos (soft delete, PROFESOR propio / COORDINADOR global) |
| `GET` | `/api/padron/moodle/sync` | `calificaciones:importar` | Sync on-demand desde Moodle |
| `POST` | `/api/padron/moodle/sync/nocturna` | `admin:configurar` | Sync programada |

## Permisos
- `calificaciones:importar` — ya existe en el seed de C-04. Se usa para todo el flujo de import/padrón.
- `admin:configurar` — para sync nocturna (configuración de tenant). Verificar si existe, si no agregar.

## Migración 006

```
alembic revision --autogenerate -m "006_create_version_padron_entrada_padron"
```

- `CREATE TABLE version_padron` con FKs a materia, cohorte, user.
- `CREATE TABLE entrada_padron` con FK a version_padron, user (nullable).
- Indexes: `(tenant_id, materia_id, cohorte_id)` en version_padron, `(version_id)` en entrada_padron.
- Partial unique index: solo una activa por (materia, cohorte).

## Dependencias nuevas

```toml
# pyproject.toml
dependencies = [
    ...,
    "openpyxl>=3.1.0",
]
```

## Tests (TDD estricto — governance MEDIO)

### Safety Net
- Ejecutar tests existentes (189 tests), capturar baseline.

### Modelos
- VersionPadron: create, activa flag, desactivar anteriores, soft delete.
- EntradaPadron: create con/sin usuario_id, bulk create, cifrado email.
- Una sola activa por (materia, cohorte).

### Repositorios
- CRUD, get_activa, desactivar_anteriores, bulk_create.
- vaciar_materia soft delete.
- Multi-tenant isolation.

### Import Flow
- Upload xlsx: archivo válido → preview con filas.
- Upload csv: archivo válido → preview.
- Upload con `?confirm=true` → versión creada y activada.
- Confirm: activa nueva, desactiva anterior.
- Vaciar materia: soft delete todas las versiones.

### Moodle WS
- Cliente: get_course_participants mockeado, timeout → retry, error → 502.

### Router
- 403 sin permiso, 400 archivo inválido, 404 materia no existe.
- Multi-tenant: padrón de tenant A no visible en B.
