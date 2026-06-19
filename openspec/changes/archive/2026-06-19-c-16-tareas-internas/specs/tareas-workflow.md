# Spec: tareas-workflow

### REQ-TAR-001: Crear tarea (F8.2)
**Scenario:** COORDINADOR crea tarea asignada a PROFESOR con descripción
**Scenario:** 403 sin tareas:gestionar

### REQ-TAR-002: Mis tareas (F8.1)
**Scenario:** PROFESOR ve solo sus tareas asignadas
**Scenario:** Filtrar por estado

### REQ-TAR-003: Admin global (F8.3)
**Scenario:** COORDINADOR ve todas las tareas con filtros
**Scenario:** Filtrar por materia, estado, asignado

### REQ-TAR-004: Estado
**Scenario:** Pendiente → En progreso → Resuelta (válido)
**Scenario:** Resuelta → Pendiente (inválido → error)
**Scenario:** Cancelar desde Pendiente o En progreso (válido)

### REQ-TAR-005: Comentarios
**Scenario:** Agregar comentario a tarea
**Scenario:** Comentarios visibles en detalle
