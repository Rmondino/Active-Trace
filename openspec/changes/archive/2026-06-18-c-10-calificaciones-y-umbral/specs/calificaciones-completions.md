# Spec: calificaciones-completions

## Overview
Capability for importing LMS completion reports to detect submitted work that has not yet been graded. Only textual-scale activities are included in the "uncorrected" report (RN-08).

## Requirements

### REQ-COM-001: Import completion report
The system MUST accept a completion status file via `POST /api/calificaciones/import/completions`.

**Scenarios:**

**Scenario: Import completion report with uncorrected submissions**
- Given: a file showing 5 activities as "completed" by students, of which 2 have no grade yet
- When: `POST /api/calificaciones/import/completions`
- Then: the response lists the 2 submissions without grades

**Scenario: Only textual activities reported**
- Given: numeric activity "Parcial 1 (Real)" with no grade and textual activity "TP Grupal" with no grade
- When: completions are processed
- Then: only "TP Grupal" appears in the report (RN-08)

**Scenario: No uncorrected submissions**
- Given: all completed activities already have grades
- When: completions are processed
- Then: response has empty `entregas_sin_corregir` list

### REQ-COM-002: Permission check
Only users with `calificaciones:importar` can import completions.

**Scenario: 403 without permission**
- Given: a user without `calificaciones:importar`
- When: `POST /api/calificaciones/import/completions`
- Then: 403 Forbidden
