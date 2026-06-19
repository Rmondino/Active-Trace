# Spec: avisos-tablon

### REQ-AVI-001: ABM avisos (F3.5)
**Scenario:** Crear aviso con alcance, severidad, vigencia, orden, requiere_ack
**Scenario:** Editar aviso existente
**Scenario:** Eliminar aviso (soft delete)
**Scenario:** 403 sin permiso avisos:publicar

### REQ-AVI-002: Visualización por scope (RN-20)
**Scenario:** Global visible para cualquier usuario del tenant
**Scenario:** PorMateria visible solo si usuario tiene asignación a esa materia
**Scenario:** PorCohorte visible solo si usuario tiene asignación a esa cohorte
**Scenario:** PorRol visible solo si usuario tiene ese rol
**Scenario:** Fuera de vigencia no se muestra (RN-18)

### REQ-AVI-003: Acuse de recibo (RN-19)
**Scenario:** Usuario acusa recibo → ack creado
**Scenario:** Stats reflejan total de acuses
**Scenario:** Duplicado rechazado

### REQ-AVI-004: Orden
**Scenario:** Avisos ordenados por orden DESC (mayor = más prioritario)

### REQ-AVI-005: Multi-tenant
**Scenario:** Avisos de tenant A no visibles en tenant B
