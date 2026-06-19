# Spec: umbral-materia

## Overview
Capability for configuring per-materia pass thresholds per teacher assignment. Each `(asignacion, materia)` pair can have its own `umbral_pct` and `valores_aprobatorios`. The system-wide default is 60%.

## Requirements

### REQ-UMB-001: Get current umbral
The system MUST provide the current umbral configuration for a materia.

**Scenarios:**

**Scenario: Get existing umbral**
- Given: an `UmbralMateria` exists with `umbral_pct=70`
- When: `GET /api/umbral?materia_id=X`
- Then: returns `{ umbral_pct: 70, valores_aprobatorios: [...] }`

**Scenario: Get umbral when not configured**
- Given: no `UmbralMateria` exists for this materia
- When: `GET /api/umbral?materia_id=X`
- Then: returns `{ umbral_pct: 60, valores_aprobatorios: ["Satisfactorio", "Supera lo esperado"] }`

### REQ-UMB-002: Update umbral
The system MUST allow updating `umbral_pct` and `valores_aprobatorios`.

**Scenarios:**

**Scenario: Update umbral_pct**
- Given: existing umbral with `umbral_pct=60`
- When: `PUT /api/umbral?materia_id=X` with `{ "umbral_pct": 75 }`
- Then: `umbral_pct` is updated to 75

**Scenario: Update valores_aprobatorios**
- Given: existing umbral
- When: `PUT /api/umbral` with `{ "valores_aprobatorios": ["Aprobado", "Muy bueno"] }`
- Then: valores_aprobatorios is updated

**Scenario: Update without permission**
- Given: a user without `calificaciones:importar`
- When: `PUT /api/umbral`
- Then: 403 Forbidden

### REQ-UMB-003: Default umbral
The system MUST provide the tenant's default umbral.

**Scenario: Get default**
- When: `GET /api/umbral/default`
- Then: returns `{ umbral_pct: 60, valores_aprobatorios: ["Satisfactorio", "Supera lo esperado"] }`
