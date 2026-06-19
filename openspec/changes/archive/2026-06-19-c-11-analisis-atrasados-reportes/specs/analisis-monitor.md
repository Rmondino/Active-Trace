# Spec: analisis-monitor

## Overview
Single monitor endpoint with scope-based filtering. `scope=propio` for TUTOR/PROFESOR (filters by user's assignments). `scope=general` for COORDINADOR/ADMIN (all students). Optional date range for general scope.

## Requirements

### REQ-MON-001: Monitor with scope propio
The system MUST return only students assigned to the current user when `scope=propio`.

**Scenarios:**

**Scenario: Monitor propio returns only user's students**
- Given: PROFESOR A has materia X, PROFESOR B has materia Y
- When: PROFESOR A queries `GET /api/analisis/monitor?scope=propio`
- Then: only materia X students are returned

### REQ-MON-002: Monitor with scope general
The system MUST return all students in the tenant when `scope=general`.

**Scenarios:**

**Scenario: Monitor general returns all students**
- Given: the tenant has 2 materias with students
- When: COORDINADOR queries `GET /api/analisis/monitor?scope=general`
- Then: all students from all materias are returned

### REQ-MON-003: Monitor filters
The system MUST support filtering by materia, regional, comision, free-text search, actividad, and estado (atrasado/no_atrasado).

**Scenarios:**

**Scenario: Filter by comision**
- Given: students in comision A and comision B
- When: `GET /api/analisis/monitor?comision=A`
- Then: only comision A students are returned

**Scenario: Filter by estado=atrasado**
- Given: 10 atrasados and 20 no-atrasados
- When: `GET /api/analisis/monitor?estado=atrasado`
- Then: only the 10 atrasados are returned

### REQ-MON-004: Date range filter (general scope only)
The system MUST support `desde` and `hasta` date filters for general scope.

**Scenario: Date range filters by import date**
- Given: grades imported in June and July
- When: `GET /api/analisis/monitor?scope=general&desde=2026-07-01&hasta=2026-07-31`
- Then: only July's data is included

### REQ-MON-005: Permission check
**Scenario: PROFESOR cannot access general scope**
- Given: a user with PROFESOR role
- When: `GET /api/analisis/monitor?scope=general`
- Then: 403 Forbidden
