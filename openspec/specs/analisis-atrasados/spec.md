# Spec: analisis-atrasados

## Overview
Compute and list students who are "atrasados" (falling behind) for a given materia. A student is atrasado if they have missing activities OR grades below the configured threshold (RN-06).

All computation logic lives in Services, never in SQL queries or Repositories.

## Requirements

### REQ-ATR-001: Compute atrasados for a materia
The system MUST compute which students are atrasados based on their grades vs the materia's umbral.

**Scenarios:**

**Scenario: Student with missing activities is atrasado**
- Given: a materia with 3 activities, student A has grades for only 2
- When: `GET /api/analisis/atrasados?materia_id=X&cohorte_id=Y`
- Then: student A is in the atrasados list with `causas.faltantes` including the missing activity

**Scenario: Student with low grade is atrasado**
- Given: a materia with umbral 60, student B has nota_numerica=45
- When: atrasados is computed
- Then: student B is in the list with `causas.baja_nota` 

**Scenario: Student with all passing grades is NOT atrasado**
- Given: student C has all activities with passing grades
- When: atrasados is computed
- Then: student C is NOT in the list

**Scenario: Atrasados detail includes causes**
- Given: student D has 1 missing activity and 1 low grade
- When: atrasados is computed
- Then: `causas` includes both `faltantes` and `baja_nota`

### REQ-ATR-002: Permission check
Only users with `atrasados:ver` can access atrasados.

**Scenario: 403 without permission**
- Given: a user without `atrasados:ver`
- When: `GET /api/analisis/atrasados`
- Then: 403 Forbidden

### REQ-ATR-003: Multi-tenant isolation
**Scenario: Atrasados isolated by tenant**
- Given: Tenant A and Tenant B have different data for the same materia_id
- When: Tenant A queries atrasados
- Then: only Tenant A's students are returned
