## Modelo de Datos

### Calificacion

```python
class Calificacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "calificacion"

    id: Mapped[str]              # UUID PK
    entrada_padron_id: Mapped[str | None]  # FK → EntradaPadron.id; nullable para calificaciones manuales
    materia_id: Mapped[str]      # FK → Materia.id
    actividad: Mapped[str]       # nombre de la actividad evaluable
    nota_numerica: Mapped[Decimal | None]  # nullable si solo hay textual
    nota_textual: Mapped[str | None]       # nullable si solo hay numérica
    aprobado: Mapped[bool]       # derivado al crear/importar
    origen: Mapped[str]          # "Importado" | "Manual"
    importado_at: Mapped[datetime]  # default now()
```

**Reglas de derivación de `aprobado`** (se computan en el service, no en SQL):
- Si `nota_numerica IS NOT NULL`: `aprobado = nota_numerica >= umbral`
- Si solo `nota_textual IS NOT NULL`: `aprobado = nota_textual IN valores_aprobatorios`
- Si ambas son NULL: `aprobado = False` (actividad sin nota)

**Unicidad**: `(tenant_id, entrada_padron_id, actividad)` — un alumno no puede tener dos calificaciones para la misma actividad importada. Para calificaciones manuales (`entrada_padron_id IS NULL`), PG permite múltiples NULLs; la deduplicación se maneja a nivel aplicación con `creado_por + actividad + materia`.

### UmbralMateria

```python
class UmbralMateria(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "umbral_materia"

    id: Mapped[str]              # UUID PK
    asignacion_id: Mapped[str]   # FK → Asignacion.id
    materia_id: Mapped[str]      # FK → Materia.id
    umbral_pct: Mapped[int]      # default 60, min 0, max 100
    valores_aprobatorios: Mapped[list[str]]  # PostgreSQL ARRAY o JSONB
```

**Unicidad**: `(tenant_id, asignacion_id, materia_id)` — un umbral por docente×materia.

## Repositorios

### CalificacionRepository

```python
class CalificacionRepository(BaseRepository[Calificacion]):
    model_class = Calificacion

    async def get_by_materia(self, materia_id: str) -> list[Calificacion]
    async def get_by_entrada(self, entrada_padron_id: str) -> list[Calificacion]
    async def bulk_create(self, calificaciones: list[Calificacion]) -> None
    async def get_actividades_by_materia(self, materia_id: str) -> list[str]  # distinct activities
    async def vaciar_materia(self, materia_id: str) -> None  # soft delete
```

### UmbralMateriaRepository

```python
class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    model_class = UmbralMateria

    async def get_by_asignacion_materia(self, asignacion_id: str, materia_id: str) -> UmbralMateria | None
    async def upsert(self, umbral: UmbralMateria) -> UmbralMateria  # crea o actualiza
    async def get_default(self, tenant_id: str) -> int  # retorna 60
```

## Flujo de Importación de Calificaciones

### Paso 1: Upload + Preview
```
POST /api/calificaciones/import
  Body: file (xlsx/csv), materia_id, cohorte_id
  → Response 200: { preview_id, actividades_detectadas, alumnos, muestra }
```

El parser detecta:
1. Participantes del padrón activo de la materia
2. Columnas de actividad (RN-01: las que terminan en `(Real)` = numéricas; el resto = textuales)
3. Para cada alumno × actividad: nota detectada

Preview responde:
```json
{
  "preview_id": "uuid",
  "actividades": [
    {"nombre": "Parcial 1 (Real)", "tipo": "numerica", "seleccionada": true},
    {"nombre": "TP Grupal", "tipo": "textual", "seleccionada": true}
  ],
  "total_alumnos": 30,
  "muestra": [{"alumno": "Juan Pérez", "actividades": {...}}]
}
```

### Paso 2: Confirmar selección
```
POST /api/calificaciones/preview/{preview_id}/confirm
  Body: { actividades_seleccionadas: ["Parcial 1 (Real)"] }
  → Response 201: { total_calificaciones, total_aprobados }
```

Al confirmar:
1. Se crean `Calificacion` para cada (alumno × actividad seleccionada)
2. Se deriva `aprobado` según RN-01/RN-02/RN-03
3. Bulk insert
4. Se registra audit `CALIFICACIONES_IMPORTAR`

### Paso 3: Upload directo
```
POST /api/calificaciones/import?confirm=true
  Body: file, materia_id, cohorte_id, actividades_seleccionadas
```
Para clients que no necesitan preview.

## Reporte de Finalización (F1.2)

```
POST /api/calificaciones/import/completions
  Body: file (xlsx/csv), materia_id
  → Response: { entregas_sin_corregir: [{alumno, actividad}], total }
```

El archivo de finalización contiene estados por alumno×actividad. Se cruza con `Calificacion` existente para detectar:
- Actividades marcadas como "completado" / "finished" en el LMS
- Pero SIN calificación registrada en el sistema
- Solo para actividades de **escala textual** (RN-08)

## Endpoints Resumen

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `POST` | `/api/calificaciones/import` | `calificaciones:importar` | Upload calificaciones, preview o confirm |
| `POST` | `/api/calificaciones/preview/{id}/confirm` | `calificaciones:importar` | Confirmar import y persistir |
| `POST` | `/api/calificaciones/import/completions` | `calificaciones:importar` | Reporte de finalización |
| `GET` | `/api/calificaciones?materia_id=X` | `calificaciones:ver` | Listar calificaciones de una materia |
| `GET` | `/api/umbral?materia_id=X` | `calificaciones:ver` | Obtener umbral actual |
| `PUT` | `/api/umbral?materia_id=X` | `calificaciones:importar` | Actualizar umbral (scope propio) |
| `GET` | `/api/umbral/default` | `calificaciones:ver` | Default del tenant |

## Permisos
- `calificaciones:importar` — ya existe del seed de C-04
- `calificaciones:ver` — ya existe del seed de C-04

## Migración 007

```
alembic revision -m "007_create_calificacion_umbral_materia"
```

- `CREATE TABLE calificacion` con FKs a entrada_padron, materia.
- `CREATE TABLE umbral_materia` con FKs a asignacion, materia.
- Index: `(tenant_id, materia_id)` en ambas.
- Unique: `(tenant_id, entrada_padron_id, actividad)` en calificacion.
- Unique: `(tenant_id, asignacion_id, materia_id)` en umbral_materia.

## Tests (TDD estricto — governance MEDIO)

### Safety Net
- Ejecutar tests existentes (231 tests), capturar baseline.

### Modelos
- Calificacion: create con numérica, textual, derivación aprobado, bulk.
- UmbralMateria: create, upsert, default.

### Repositorios
- CRUD, bulk_create, get_by_materia, upsert, get_default.
- Multi-tenant isolation.

### Import Flow
- Upload xlsx con columnas (Real) → numéricas detectadas.
- Upload csv → preview con actividades.
- Preview → confirm → bulk create + audit.
- Actividades seleccionadas filtran lo que se importa.
- Confirm sin preview previo → directo.

### Completions
- Reporte de finalización → entregas sin corregir.
- Solo textuales (RN-08).

### Umbral
- GET default → 60.
- PUT actualiza umbral.
- PUT sin permiso → 403.

### Router
- 403 sin permiso, 400 archivo inválido, 404 materia no existe.
- Multi-tenant isolation.
- Audit `CALIFICACIONES_IMPORTAR`.
