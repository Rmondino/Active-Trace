# Spec: calificaciones-import

## Overview
Capability for importing student grades from LMS export files (.xlsx/.csv) with preview, activity selection, and confirmation. Grades are linked to the active `VersionPadron` entries for the materia. Supports both imported (from LMS) and manual grade origins.

## Requirements

### REQ-CAL-001: Upload grades file
The system MUST accept `.xlsx` and `.csv` grade files via `POST /api/calificaciones/import`.

**Scenarios:**

**Scenario: Upload valid file with numeric columns**
- Given: an `.xlsx` file with columns `Alumno`, `Parcial 1 (Real)`, `TP Grupal`
- When: `POST /api/calificaciones/import` with `file`, `materia_id`, `cohorte_id`
- Then: it detects `Parcial 1 (Real)` as numeric (RN-01), `TP Grupal` as textual, returns preview

**Scenario: Upload without (Real) columns**
- Given: a file where no column header ends with `(Real)`
- When: upload
- Then: all detected columns are marked as `textual`

**Scenario: Upload invalid file type**
- Given: a `.pdf` file
- When: upload
- Then: 400 Bad Request

### REQ-CAL-002: Preview with activity selection
The preview MUST show detected activities with type (numeric/textual) and allow selecting which to include.

**Scenarios:**

**Scenario: Preview shows activities detected**
- Given: a file with 3 columns
- When: preview is generated
- Then: `actividades` contains 3 entries with `nombre`, `tipo`, `seleccionada` (default true)

**Scenario: Preview matches students to padron**
- Given: the active padron has 20 students
- When: preview is generated
- Then: `total_alumnos` is 20 and `muestra` contains up to 5 rows

### REQ-CAL-003: Confirm import
The system MUST persist grades when the preview is confirmed.

**Scenarios:**

**Scenario: Confirm creates Calificacion records**
- Given: a preview with 2 selected activities for 20 students
- When: `POST /api/calificaciones/preview/{preview_id}/confirm`
- Then: 40 `Calificacion` records are created with `origen="Importado"`

**Scenario: Confirm derives aprobado correctly**
- Given: a numeric grade of 75 with umbral 60
- When: confirmed
- Then: `aprobado = True`
- Given: a numeric grade of 45 with umbral 60
- Then: `aprobado = False`

**Scenario: Confirm with textual "Satisfactorio"**
- Given: a textual grade "Satisfactorio" and it's in valores_aprobatorios
- When: confirmed
- Then: `aprobado = True`

**Scenario: Direct import with ?confirm=true**
- Given: a valid file and selected activities via query param
- When: `POST /api/calificaciones/import?confirm=true`
- Then: grades are persisted directly

### REQ-CAL-004: Audit
The system MUST register an audit entry with code `CALIFICACIONES_IMPORTAR` when grades are imported.

**Scenario: Audit log on import**
- Given: a confirmed import with 40 grades
- Then: an `AuditLog` entry exists with `accion="CALIFICACIONES_IMPORTAR"` and `detalle` containing `total`

### REQ-CAL-005: Multi-tenant isolation
Each tenant MUST only see their own grades.

**Scenario: Grades isolated by tenant**
- Given: Tenant A has grades, Tenant B does not
- When: Tenant B queries grades for the same materia_id
- Then: Tenant B sees empty results
