# Spec: padron-moodle-sync

## Overview
Capability for synchronizing student rosters from Moodle Web Services, supporting on-demand sync and scheduled nightly sync. Provides a fallback to manual import when Moodle is unavailable.

## Requirements

### REQ-MOODLE-001: Moodle WS client
The system MUST provide a dedicated client for Moodle Web Services communication.

**Scenarios:**

**Scenario: Get course participants**
- Given: a valid Moodle URL, token, and course_id
- When: `get_course_participants(course_id)` is called
- Then: the client returns a list of participants with `nombre`, `apellidos`, `email`

**Scenario: Moodle timeout → retry**
- Given: Moodle is slow to respond
- When: the client sends a request
- Then: it retries up to 3 times with exponential backoff before raising `MoodleWSError`

**Scenario: Moodle unavailable → 502 mapping**
- Given: Moodle is offline or returns errors
- When: the client request fails after retries
- Then: `MoodleWSError` is raised, which the API maps to HTTP 502 Bad Gateway

**Scenario: Invalid token**
- Given: an invalid Moodle token
- When: the client sends a request
- Then: `MoodleWSAuthError` is raised

### REQ-MOODLE-002: On-demand sync
The system MUST allow triggering a Moodle sync on-demand.

**Scenarios:**

**Scenario: Sync creates version from Moodle data**
- Given: a materia linked to a Moodle course
- When: `GET /api/padron/moodle/sync?materia_id=X&cohorte_id=Y&course_id=Z`
- Then: a new `VersionPadron` is created with `origen="moodle"` and the synced participants as `EntradaPadron`

**Scenario: Sync with Moodle error**
- Given: Moodle is unavailable
- When: `GET /api/padron/moodle/sync`
- Then: 502 Bad Gateway with error description

### REQ-MOODLE-003: Scheduled sync
The system MUST support a scheduled (nightly) sync that processes all materias with Moodle integration configured.

**Scenarios:**

**Scenario: Nocturnal sync processes all configured materias**
- Given: 3 materias with Moodle integration
- When: `POST /api/padron/moodle/sync/nocturna` is called by an admin
- Then: all 3 are synced, returning a summary of results

**Scenario: Nocturnal sync requires admin permission**
- Given: a user without `admin:configurar`
- When: `POST /api/padron/moodle/sync/nocturna`
- Then: 403 Forbidden
