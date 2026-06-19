## Why

El sistema necesita un padrón de alumnos por materia y cohorte para poder analizar calificaciones, detectar atrasados y comunicarse con estudiantes. El padrón debe ser **versionado**: cada importación reemplaza al anterior conservando el histórico.

Además, la integración con **Moodle Web Services** permite sincronizar usuarios y actividades sin intervención manual, con sync nocturna y on-demand. Sin esta capa, el sistema depende exclusivamente de uploads manuales de archivos, lo cual es frágil y poco escalable.

## What Changes

### Modelos VersionPadron + EntradaPadron
- `VersionPadron`: representa una versión del padrón para una materia×cohorte. Una sola versión activa por combinación.
- `EntradaPadron`: cada alumno dentro de una versión. Desnormaliza nombre/apellidos para histórico. `usuario_id` nullable (alumno puede no tener cuenta aún).

### Import de padrón (manual)
- Endpoint `POST /api/padron/import` que recibe un archivo `.xlsx` o `.csv`
- Procesa el archivo y devuelve una **vista previa** (N filas detectadas, columnas mapeadas)
- Endpoint `POST /api/padron/{version_id}/confirm` que activa la versión (desactivando la anterior)
- Vaciar datos de materia: `DELETE /api/padron/materia/{materia_id}` (soft delete de versiones)

### Moodle Web Services
- Cliente dedicado `integrations/moodle_ws.py` para comunicación con Moodle
- Sync de usuarios: obtiene listado de participantes de un curso Moodle
- Sync nocturna programada (vía worker) + on-demand desde API
- Errores mapean a 502 con reintento configurable

### Reglas de negocio
- **Upsert destructivo**: activar una nueva versión desactiva la anterior (RN-05)
- **Entrada sin usuario_id**: se permite (alumno sin cuenta en el sistema aún)
- **Auditoría**: cada import y activación genera `PADRON_CARGAR`
- **Moodle WS**: timeout configurable, reintento 3 veces, fallback a import manual

### Dependencias nuevas
- `openpyxl` para parseo de `.xlsx`
- `csv` módulo estándar para `.csv`

## Capabilities

### New Capabilities
- `padron-import`: Upload de archivo, parseo, vista previa, confirmación y activación de versión.
- `padron-moodle-sync`: Sincronización de padrón desde Moodle Web Services (nocturna + on-demand).
- `padron-clear`: Vaciar datos de una materia (soft delete versionado).

### Modified Capabilities
- *(Ninguna)*

## Impact

- **Modelos**: `backend/app/models/version_padron.py`, `backend/app/models/entrada_padron.py` (nuevos).
- **Repositorios**: `VersionPadronRepository`, `EntradaPadronRepository`.
- **Integración**: `backend/app/integrations/moodle_ws.py` (nuevo — cliente Moodle WS).
- **Router**: `backend/app/routers/padron.py` (nuevo — import + preview + confirm + vaciar).
- **Worker**: tarea programada para sync nocturna Moodle.
- **Dependencias**: `openpyxl` agregado a `pyproject.toml`.
- **Auditoría**: registro `PADRON_CARGAR` con detalle de filas importadas.
- **Migración 006**: `version_padron`, `entrada_padron`.
