## ADDED Requirements

### Requirement: Mis tareas

El sistema SHALL mostrar las tareas asignadas al usuario actual con filtro por estado. SHALL permitir cambiar el estado y agregar comentarios.

#### Scenario: Ver mis tareas

- **WHEN** un usuario navega a "Mis tareas"
- **THEN** se muestra una tabla con sus tareas pendientes

#### Scenario: Cambiar estado de tarea

- **WHEN** el usuario cambia el estado de una tarea
- **THEN** el sistema llama a `PATCH /api/tareas/{id}/estado`

#### Scenario: Agregar comentario

- **WHEN** el usuario agrega un comentario a una tarea
- **THEN** el sistema llama a `POST /api/tareas/{id}/comentarios`

### Requirement: Asignar tarea a docente

El sistema SHALL permitir al COORDINADOR crear una tarea asignada a un docente, con descripción, materia opcional y contexto opcional.

### Requirement: Admin global de tareas

El sistema SHALL permitir al COORDINADOR ver todas las tareas del tenant con filtros por estado, materia y usuario asignado.
