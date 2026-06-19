# Spec: padron-import

## Overview
Capability for importing student rosters (padrón) from `.xlsx` or `.csv` files, with versioned storage. Supports a two-step flow (preview → confirm) or direct import. Each import creates a new `VersionPadron` that replaces the previously active version for the same `(materia, cohorte)`.

## Requirements

### REQ-IMPORT-001: Upload and parse file
The system MUST accept `.xlsx` and `.csv` files via `POST /api/padron/import`.

**Scenarios:**

**Scenario: Upload valid xlsx file**
- Given: a valid `.xlsx` file with columns `nombre`, `apellidos`, `email`, `comision`, `regional`
- When: `POST /api/padron/import` with `file`, `materia_id`, `cohorte_id`
- Then: the system returns a preview with `total_filas`, `columnas`, and a `muestra` of up to 5 rows

**Scenario: Upload valid csv file**
- Given: a valid `.csv` file with columns `nombre`, `apellidos`, `email`, `comision`, `regional`
- When: `POST /api/padron/import` with `file`, `materia_id`, `cohorte_id`
- Then: the system returns a preview with the same structure

**Scenario: Upload with invalid file type**
- Given: a `.pdf` file
- When: `POST /api/padron/import` with `file`
- Then: the system returns 400 Bad Request: "Formato de archivo no soportado. Use .xlsx o .csv"

**Scenario: Upload with missing required columns**
- Given: an `.xlsx` file missing the `email` column
- When: `POST /api/padron/import`
- Then: the system returns 400: "Faltan columnas requeridas: email"

### REQ-IMPORT-002: Preview with sample rows
The preview MUST include a sample of the first rows and indicate any parsing errors per row.

**Scenarios:**

**Scenario: Preview shows first 5 rows**
- Given: a file with 100 rows
- When: preview is generated
- Then: `muestra` contains at most 5 rows

**Scenario: Preview reports malformed rows**
- Given: a file where row 3 has an empty email
- When: preview is generated
- Then: `errores` includes an entry for row 3 with a description

### REQ-IMPORT-003: Confirm preview and activate version
The system MUST allow confirming a preview to persist the data and activate the version.

**Scenarios:**

**Scenario: Confirm creates version and entries**
- Given: a valid preview with 10 rows
- When: `POST /api/padron/preview/{preview_id}/confirm`
- Then: a new `VersionPadron` is created with `activa=True`, 10 `EntradaPadron` rows, and the previous active version for the same `(materia, cohorte)` is deactivated

**Scenario: Confirm without prior preview (direct import)**
- Given: a valid file with `?confirm=true`
- When: `POST /api/padron/import?confirm=true`
- Then: the version is created directly, returning `{ version_id, filas_importadas }`

**Scenario: Confirm with unknown preview_id**
- Given: a non-existent preview_id
- When: `POST /api/padron/preview/{preview_id}/confirm`
- Then: 404 Not Found

### REQ-IMPORT-004: Upsert destructivo (RN-05)
Activating a new version MUST deactivate the previously active version for the same `(materia, cohorte)`.

**Scenarios:**

**Scenario: New version deactivates old one**
- Given: an active `VersionPadron` for `(materia-X, cohorte-Y)`
- When: a new version is confirmed for `(materia-X, cohorte-Y)`
- Then: the old version has `activa=False`, the new one has `activa=True`

**Scenario: Different cohorte not affected**
- Given: an active version for `(materia-X, cohorte-Y)` and a new import for `(materia-X, cohorte-Z)`
- When: the new version is confirmed
- Then: the `(materia-X, cohorte-Y)` version remains active

### REQ-IMPORT-005: Entrada sin usuario_id permitida
Entries MAY have `usuario_id = NULL` for students who do not yet have an account in the system.

**Scenarios:**

**Scenario: Import with no existing user**
- Given: a file with an email not linked to any `User` in the system
- When: the import is confirmed
- Then: the `EntradaPadron` is created with `usuario_id = NULL`

**Scenario: Import with existing user**
- Given: a file with an email matching an existing `User`
- When: the import is confirmed
- Then: the `EntradaPadron` is created with the matching `usuario_id`

### REQ-IMPORT-006: List versions
The system MUST provide a way to list all versions for a `(materia, cohorte)`.

**Scenarios:**

**Scenario: List versions for a materia**
- Given: 3 versions for `(materia-X, cohorte-Y)`
- When: `GET /api/padron/versiones?materia_id=X&cohorte_id=Y`
- Then: the response contains 3 entries sorted by `cargado_at` descending

**Scenario: List versions without permission**
- Given: a user without `calificaciones:importar`
- When: `GET /api/padron/versiones`
- Then: 403 Forbidden

### REQ-IMPORT-007: Multi-tenant isolation
Each tenant MUST only see their own versions and entries.

**Scenario: Versiones isolated by tenant**
- Given: Tenant A has a version, Tenant B does not
- When: Tenant B lists versions for the same materia_id
- Then: Tenant B sees an empty list
