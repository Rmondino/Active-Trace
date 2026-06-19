# Spec: panel-auditoria

### REQ-PAN-001: Acciones por día
**Scenario:** Agrupa audit_log por día con conteo
**Scenario:** Filtra por rango de fechas

### REQ-PAN-002: Comunicaciones por docente
**Scenario:** Agrupa Comunicacion por enviado_por y estado

### REQ-PAN-003: Interacciones por docente×materia
**Scenario:** Agrupa audit_log por actor_id, materia_id, accion
**Scenario:** Filtra por rango de fechas

### REQ-PAN-004: Últimas acciones
**Scenario:** Retorna últimas N acciones (default 200)
**Scenario:** Límite configurable

### REQ-PAN-005: Log completo (F9.2)
**Scenario:** Filtros por acción, materia, actor, fechas
**Scenario:** 403 sin permiso auditoria:ver

### REQ-PAN-006: Scope propio
**Scenario:** COORDINADOR solo ve sus propias acciones
**Scenario:** ADMIN ve todo el tenant
