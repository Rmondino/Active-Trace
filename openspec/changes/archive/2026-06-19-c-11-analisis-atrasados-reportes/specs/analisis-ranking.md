# Spec: analisis-ranking

## Overview
Rank students by number of approved activities, descending. Only students with at least 1 approved activity are included (RN-09). All computation in Services.

## Requirements

### REQ-RNK-001: Ranking by approved activities
The system MUST return students ordered by approved activities count descending.

**Scenarios:**

**Scenario: Ranking returns students sorted desc**
- Given: student A has 4 approved, student B has 2 approved, student C has 1 approved
- When: `GET /api/analisis/ranking?materia_id=X`
- Then: the order is A, B, C

**Scenario: Ranking excludes students with 0 approved**
- Given: student D has 0 approved activities
- When: ranking is computed
- Then: student D is NOT in the list (RN-09)

**Scenario: Ranking with textual grades**
- Given: student E has a textual grade "Satisfactorio" which counts as approved
- When: ranking is computed
- Then: student E is included with the activity counted

### REQ-RNK-002: Ranking includes detail
**Scenario: Ranking entries include counts**
- Given: a ranking with student A (4/5 approved)
- Then: response includes `{ alumno, aprobadas, total, porcentaje }`
