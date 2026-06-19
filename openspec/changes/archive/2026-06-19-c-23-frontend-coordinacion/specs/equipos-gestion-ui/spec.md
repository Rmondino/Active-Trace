## ADDED Requirements

### Requirement: Listado de asignaciones docentes

El sistema SHALL mostrar las asignaciones docentes con filtros por materia, carrera, cohorte, usuario y rol. SHALL usar TanStack Table con sorting y paginación. Cada fila SHALL mostrar usuario, rol, materia, carrera, cohorte, comisiones, vigencia.

#### Scenario: Listado con filtros

- **WHEN** el COORDINADOR navega a la sección de equipos
- **THEN** se muestra una tabla con todas las asignaciones y filtros disponibles

### Requirement: Asignación masiva

El sistema SHALL permitir asignar un rol a múltiples docentes en una materia/carrera/cohorte con un solo formulario. SHALL incluir campos: docentes (multi-select), rol, materia, carrera, cohorte, comisiones, responsable, fechas de vigencia.

#### Scenario: Asignación masiva exitosa

- **WHEN** el COORDINADOR completa el formulario de asignación masiva
- **THEN** el sistema llama a `POST /api/equipos/asignaciones/masiva`
- **AND** muestra el total de asignaciones creadas

### Requirement: Clonar equipo entre cohortes

El sistema SHALL permitir clonar las asignaciones de un equipo de origen (materia+carrera+cohorte) a un destino (materia+carrera+cohorte) con nuevas fechas de vigencia.

#### Scenario: Clonación exitosa

- **WHEN** el COORDINADOR selecciona origen y destino y ejecuta la clonación
- **THEN** el sistema llama a `POST /api/equipos/clonar`
- **AND** muestra el total de asignaciones clonadas

### Requirement: Modificar vigencia en bloque

El sistema SHALL permitir modificar las fechas de vigencia de todas las asignaciones de una materia+carrera+cohorte.

### Requirement: Exportar equipo

El sistema SHALL proveer un botón "Exportar" que descargue un XLSX del equipo (`GET /api/equipos/export`).
