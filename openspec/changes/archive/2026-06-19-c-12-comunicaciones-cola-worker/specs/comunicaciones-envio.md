# Spec: comunicaciones-envio

## Overview
Capability for sending communications to students via email, with mandatory preview (RN-16), async dispatch queue (RN-15), and configurable human approval (RN-17).

## Requirements

### REQ-COM-001: Preview messages (RN-16)
The system MUST render a preview of messages before enqueuing.

**Scenarios:**

**Scenario: Preview renders templates with student data**
- Given: a template `"Hola {alumno_nombre}"` and a student named "Juan"
- When: `POST /api/comunicaciones/preview` with the template and student IDs
- Then: preview includes `{ asunto: "...", cuerpo: "Hola Juan" }`

**Scenario: Preview returns a token**
- Given: a valid preview request
- When: preview is generated
- Then: response includes a `preview_token`

### REQ-COM-002: Preview token expires (30 min)
The preview token MUST expire after 30 minutes.

**Scenario: Expired token rejected**
- Given: a preview_token generated 31 minutes ago
- When: `POST /api/comunicaciones/enviar` with the expired token
- Then: 400 Bad Request: "Preview expirado"

### REQ-COM-003: Preview token single-use
The preview token MUST be invalidated after being used.

**Scenario: Used token rejected**
- Given: a successful enqueue with a preview_token
- When: `POST /api/comunicaciones/enviar` again with the same token
- Then: 400 Bad Request: "Preview ya utilizado"

### REQ-COM-004: Enqueue messages
The system MUST create Comunicacion records in Pendiente state.

**Scenarios:**

**Scenario: Enqueue creates Pendiente records**
- Given: 3 recipients
- When: `POST /api/comunicaciones/enviar` with valid preview_token
- Then: 3 Comunicacion records created with `estado="Pendiente"`, same `lote_id`

**Scenario: Enqueue without preview returns 400**
- Given: no preview_token
- When: `POST /api/comunicaciones/enviar`
- Then: 400 Bad Request: "Preview requerido"

**Scenario: Enqueue assigns same lote_id to batch**
- Given: a batch of messages
- When: enqueued
- Then: all messages share the same `lote_id`

### REQ-COM-005: Approval flow (RN-17)
The system MUST support approval before dispatch if configured.

**Scenarios:**

**Scenario: Approval required → stays Pendiente**
- Given: a tenant with `aprobacion_requerida=true`
- When: messages are enqueued
- Then: they stay `estado="Pendiente"` with `aprobado_por IS NULL`

**Scenario: Approve batch transitions to ready**
- Given: a lote with 10 Pendiente messages
- When: `POST /api/comunicaciones/aprobar/lote/{lote_id}` by a user with `comunicacion:aprobar`
- Then: all 10 messages have `aprobado_por` and `aprobado_at` set

**Scenario: Reject message → Cancelado**
- Given: a Pendiente message
- When: `POST /api/comunicaciones/rechazar/{id}`
- Then: `estado = "Cancelado"`

### REQ-COM-006: State machine (RN-15)
The system MUST enforce valid state transitions and reject invalid ones.

**Scenarios:**

**Scenario: Pendiente → Enviando → Enviado (valid)**
- Given: a Pendiente message
- When: worker transitions to Enviando then Enviado
- Then: final state is Enviado

**Scenario: Cancel from Pendiente (valid)**
- Given: a Pendiente message
- When: rejected
- Then: `estado = "Cancelado"` — valid transition

**Scenario: Cancel from Enviado (INVALID)**
- Given: an Enviado message
- When: `POST /api/comunicaciones/rechazar/{id}`
- Then: 400 Bad Request: "Transición inválida: Enviado → Cancelado"

**Scenario: Enviar from Cancelado (INVALID)**
- Given: a Cancelado message
- When: worker tries to transition to Enviando
- Then: transition is rejected

### REQ-COM-007: Tracking
The system MUST provide message status tracking.

**Scenarios:**

**Scenario: Get tracking by materia**
- Given: a materia with 5 messages across states
- When: `GET /api/comunicaciones?materia_id=X`
- Then: returns 5 messages with estado, destinatario_mask, lote_id

**Scenario: Get pending approval queue**
- Given: 3 messages pending approval
- When: `GET /api/comunicaciones/pendientes-aprobacion`
- Then: returns grouped by lote with counts

**Scenario: 403 without permission**
- Given: a user without `comunicacion:enviar`
- When: any communications endpoint
- Then: 403 Forbidden
