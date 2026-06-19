## Why

Con C-09 tenemos el padrón versionado. El siguiente paso lógico es importar las **calificaciones** de los alumnos vinculadas a ese padrón. Sin calificaciones no podemos analizar atrasados, detectar entregas sin corregir, ni comunicarnos con los estudiantes en riesgo.

Además, cada materia necesita un **umbral de aprobación** configurable por docente (RN-03, default 60%) para que el sistema pueda derivar automáticamente si un alumno aprobó o no cada actividad.

## What Changes

### Modelos Calificacion + UmbralMateria

- **Calificacion**: nota por alumno×actividad. Soporta numérica (`nota_numerica`) y textual (`nota_textual`). `aprobado` es un campo **derivado** (se computa al crear/importar según RN-01/RN-02/RN-03). FK a `EntradaPadron` (no a User directo).
- **UmbralMateria**: configurable por `(asignacion_id, materia_id)`. Contiene `umbral_pct` (default 60) y `valores_aprobatorios` (lista textual). Si no existe, se usa el default del tenant.

### Import de calificaciones (F1.1)
- `POST /api/calificaciones/import` — sube archivo xlsx/csv con notas
- Detecta automáticamente columnas de nota numérica (RN-01: encabezados que terminan en `(Real)`)
- Preview: muestra actividades detectadas, el usuario selecciona cuáles incluir
- Confirmación: persiste calificaciones, deriva `aprobado`, genera audit `CALIFICACIONES_IMPORTAR`
- Participantes vinculados al `VersionPadron` activo de la materia×cohorte

### Import de reporte de finalización (F1.2)
- `POST /api/calificaciones/import/completions` — archivo con estados de finalización
- Detecta TP "completado" SIN calificación aún (RN-07)
- Reporta entregas sin corregir (solo actividades textuales, RN-08)

### Umbral por materia (F2.1)
- `GET /api/umbral?materia_id=X` — obtener configuración actual
- `PUT /api/umbral?materia_id=X` — actualizar `umbral_pct` y `valores_aprobatorios`
- `GET /api/umbral/default` — obtener el default del tenant
- Scope: solo el docente asignado a esa materia puede modificar su umbral

### Reglas de negocio
- **RN-01**: columnas con `(Real)` al final → nota numérica
- **RN-02**: "Satisfactorio" y "Supera lo esperado" → aprobado textual
- **RN-03**: umbral default 60%, configurable por docente×materia
- **RN-07**: cruce reporte de finalización vs calificaciones → entregas sin corregir
- **RN-08**: solo actividades textuales en la tabla de "sin corregir"
- **RN-04**: datos scope-isolated por `(usuario_id × materia_id)` — el import de un docente no afecta datos de otro

### Scope isolation (RN-04)
Cada `Calificacion` se asocia al `VersionPadron` activo del docente que importa. Como el padrón es por `(materia, cohorte)`, y el docente importa su propio padrón (C-09), las calificaciones quedan naturalmente aisladas por `(usuario_id, materia_id)`.

## Capabilities

### New Capabilities
- `calificaciones-import`: Upload, preview, y confirmación de calificaciones desde archivo LMS.
- `calificaciones-completions`: Import de reporte de finalización + detección de entregas sin corregir.
- `umbral-materia`: Configuración de umbral de aprobación por docente×materia.

## Impact

- **Modelos**: `backend/app/models/calificacion.py`, `umbral_materia.py` (nuevos).
- **Repositorios**: `CalificacionRepository`, `UmbralMateriaRepository`.
- **Servicios**: `CalificacionesParserService` (parseo + preview + derivación aprobado), `UmbralService`.
- **Router**: `backend/app/routers/calificaciones.py`, `umbral.py` (nuevos).
- **Migración 007**: `calificacion`, `umbral_materia`.
- **Auditoría**: código `CALIFICACIONES_IMPORTAR`.
- **Dependencias**: ninguna nueva (reusa openpyxl de C-09).
