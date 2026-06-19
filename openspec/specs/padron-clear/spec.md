# Spec: padron-clear

## Overview
Capability for clearing (vaciar) all versioned data for a given materia. Implements F1.5 (Vaciar datos de una materia) with RN-04: clears import data without affecting other materias or other teachers' data.

## Requirements

### REQ-CLEAR-001: Vaciar materia (soft delete)
The system MUST soft-delete all `VersionPadron` and `EntradaPadron` records for a given materia.

**Scenarios:**

**Scenario: Vaciar materia soft deletes all versions**
- Given: a materia with 3 versiones
- When: `DELETE /api/padron/materia/{materia_id}`
- Then: all 3 versiones have `deleted_at` set (soft delete)

**Scenario: Vaciar does not affect other materias**
- Given: 2 materias, each with versions
- When: `DELETE /api/padron/materia/{materia_1}`
- Then: materia_2 versions remain active (no `deleted_at`)

### REQ-CLEAR-002: Vaciar generates audit PADRON_CARGAR
The system MUST register an audit entry with code `PADRON_CARGAR` (cumple RN-04) when data is cleared.

**Scenarios:**

**Scenario: Audit log entry on vaciar**
- Given: a materia with versions
- When: `DELETE /api/padron/materia/{materia_id}` is called
- Then: an `AuditLog` entry is created with `accion="PADRON_CARGAR"` and `detalle` including `materia_id` and `versiones_afectadas`

### REQ-CLEAR-003: Permission check
Only users with `calificaciones:importar` and `(propio)` scope (PROFESOR for own materias) or global scope (COORDINADOR) can vaciar.

**Scenarios:**

**Scenario: User without permission gets 403**
- Given: a user without `calificaciones:importar`
- When: `DELETE /api/padron/materia/{materia_id}`
- Then: 403 Forbidden

**Scenario: Multi-tenant isolation**
- Given: Tenant A materias with versions
- When: Tenant B tries to vaciar Tenant A's materia
- Then: 404 Not Found (materia does not exist in tenant B's scope)
