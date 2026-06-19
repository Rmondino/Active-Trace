# Spec: encuentros-slots

## Overview
Create and manage encounter slots (recurrent or single), generate instances, edit instances independently.

### REQ-ENC-001: Crear slot recurrente (RN-13)
**Scenario:** Slot recurrente genera N instancias semanales desde fecha_inicio
**Scenario:** Slot único con fecha_unica genera 1 instancia
**Scenario:** Recurrente y único son excluyentes (validación)

### REQ-ENC-002: Editar instancia (RN-14)
**Scenario:** Editar estado de instancia no afecta slot
**Scenario:** Editar meet_url de instancia no afecta slot
**Scenario:** Editar instancia de slot diferente no afecta otras

### REQ-ENC-003: Contenido aula (F6.4)
**Scenario:** Genera HTML con tabla de encuentros de la materia

### REQ-ENC-004: Vista admin (F6.5)
**Scenario:** COORDINADOR ve todos los encuentros del tenant
**Scenario:** 403 para PROFESOR sin permiso global

# Spec: guardias-registro

### REQ-GUA-001: Registrar guardia (F6.6)
**Scenario:** TUTOR registra guardia propia
**Scenario:** COORDINADOR registra cualquier guardia

### REQ-GUA-002: Listar guardias
**Scenario:** Filtrar por materia
**Scenario:** Multi-tenant isolation

### REQ-GUA-003: Exportar guardias
**Scenario:** Genera xlsx válido con columnas correctas
