# Spec: analisis-reportes

## Overview
Quick reports and final grades aggregation for a materia. All computation in Services.

## Requirements

### REQ-RPT-001: Reporte rápido
The system MUST return aggregate metrics for a materia.

**Scenarios:**

**Scenario: Reporte with populated data**
- Given: a materia with 30 students and 5 activities
- When: `GET /api/analisis/reporte-rapido?materia_id=X`
- Then: response includes `total_alumnos`, `total_actividades`, `alumnos_atrasados`, `tasa_aprobacion_gral`, per-activity stats

### REQ-RPT-002: Notas finales
The system MUST return final grades grouped per student.

**Scenarios:**

**Scenario: Notas finales with numeric and textual grades**
- Given: a student with one numeric (75) and one textual ("Satisfactorio") grade
- When: `GET /api/analisis/notas-finales?materia_id=X&cohorte_id=Y`
- Then: response includes `promedio_numerico`, `aprobadas`, `total_actividades`

**Scenario: Empty materia**
- Given: a materia with no grades yet
- When: reporte-rapido is queried
- Then: returns zero counts, not an error
