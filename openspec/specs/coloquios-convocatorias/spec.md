# Spec: coloquios-convocatorias

### REQ-COL-001: Crear convocatoria (F7.3)
**Scenario:** Crear convocatoria con materia, cohorte, instancia, cupo_por_dia
**Scenario:** Crear sin permisos → 403

### REQ-COL-002: Listar convocatorias (F7.4)
**Scenario:** COORDINADOR ve todas
**Scenario:** ALUMNO ve solo las de su cohorte

### REQ-COL-003: Reservar turno
**Scenario:** Alumno reserva con cupo disponible
**Scenario:** Alumno reserva sin cupo → 400 "Cupo completo"
**Scenario:** Alumno reserva duplicado → 400
**Scenario:** Alumno reserva en evaluación inactiva → 400

### REQ-COL-004: Cancelar reserva
**Scenario:** Alumno cancela su propia reserva
**Scenario:** Alumno cancela reserva ajena → 403

### REQ-COL-005: Resultados
**Scenario:** Registrar nota final
**Scenario:** Ver resultados de convocatoria

### REQ-COL-006: Métricas (F7.1)
**Scenario:** Detalle muestra convocados, reservas activas, cupos libres

### REQ-COL-007: Admin global (F7.5)
**Scenario:** ADMIN ve todas las convocatorias con métricas consolidadas
