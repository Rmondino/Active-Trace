# Spec: equipos-gestion

## Overview
Team management capabilities: view my assignments, manage all assignments, bulk assign, clone between periods, update validity, and export. All operations over the existing Asignacion model.

## Requirements

### REQ-EQ-001: Mis equipos (F4.2)
The system MUST return the authenticated user's assignments with expanded context.

**Scenarios:**

**Scenario: User sees their own assignments**
- Given: a PROFESOR with 3 asignaciones
- When: `GET /api/equipos/mis-equipos`
- Then: returns 3 entries with materia, carrera, cohorte, rol, vigencia expanded

**Scenario: Filter by estado=vigente**
- Given: 2 vigentes and 1 no vigente
- When: `GET /api/equipos/mis-equipos?estado=vigente`
- Then: returns only the 2 vigentes

**Scenario: Filter by materia**
- Given: assignments in 2 materias
- When: `GET /api/equipos/mis-equipos?materia_id=X`
- Then: returns only assignments for materia X

### REQ-EQ-002: Gestión de asignaciones (F4.3)
The system MUST allow COORDINADOR/ADMIN to view all assignments with filters.

**Scenario: COORDINADOR sees all**
- Given: 2 users with assignments
- When: `GET /api/equipos/asignaciones` by a COORDINADOR
- Then: returns all assignments in the tenant

**Scenario: Filter by rol**
- Given: PROFESOR and TUTOR assignments
- When: `GET /api/equipos/asignaciones?rol=PROFESOR`
- Then: only PROFESOR assignments returned

**Scenario: PROFESOR gets 403**
- Given: a user with PROFESOR role
- When: `GET /api/equipos/asignaciones`
- Then: 403 Forbidden

### REQ-EQ-003: Asignación masiva (F4.4)
The system MUST create multiple assignments in one operation.

**Scenario: Assign 3 docentes to same materia**
- Given: 3 docente IDs
- When: `POST /api/equipos/asignaciones/masiva` with those IDs + materia + carrera + cohorte + rol + vigencia
- Then: 3 Asignacion records created with the same context

**Scenario: Masiva with comisiones**
- Given: comisiones ["A", "B"]
- When: masiva
- Then: each Asignacion has comisiones ["A", "B"]

**Scenario: 403 without equipos:asignar**
- Given: user without equipos:asignar
- When: POST masiva
- Then: 403

### REQ-EQ-004: Clonar equipo (F4.5, RN-12)
The system MUST duplicate vigentes asignaciones from source to destination cohort.

**Scenario: Clone preserves user, rol, comisiones**
- Given: source equipo has 3 vigentes asignaciones with various roles
- When: `POST /api/equipos/clonar` with source and destination
- Then: 3 new Asignacion created with same usuario_id, rol, comisiones but new fechas and new context

**Scenario: Clone only copies vigentes**
- Given: source has 2 vigentes and 1 vencida
- When: clone
- Then: only 2 cloned (the vencida is skipped)

**Scenario: Clone updates audit**
- When: clone is executed
- Then: audit `ASIGNACION_MODIFICAR` is logged

### REQ-EQ-005: Vigencia general (F4.6)
The system MUST update desde/hasta for all assignments matching a filter.

**Scenario: Update vigencia for equipo**
- Given: 5 asignaciones for (materia X, carrera Y, cohorte Z)
- When: `PATCH /api/equipos/vigencia` with new desde/hasta
- Then: all 5 have the new dates

**Scenario: Only matching assignments updated**
- Given: 3 for cohorte Z and 2 for cohorte W
- When: PATCH for cohorte Z
- Then: only the 3 for cohorte Z are updated

### REQ-EQ-006: Exportar equipo (F4.7)
The system MUST generate an xlsx file with assignment details.

**Scenario: Export returns valid xlsx**
- Given: an equipo with 5 asignaciones
- When: `GET /api/equipos/export?materia_id=X&carrera_id=Y&cohorte_id=Z`
- Then: response has Content-Type xlsx and valid workbook bytes

**Scenario: Export columns correct**
- When: export is generated
- Then: xlsx has columns: Docente, Email, Rol, Comisiones, Materia, Carrera, Cohorte, Desde, Hasta, Vigente, Responsable

### REQ-EQ-007: Multi-tenant isolation
**Scenario:** Tenant A assignments not visible to Tenant B.
