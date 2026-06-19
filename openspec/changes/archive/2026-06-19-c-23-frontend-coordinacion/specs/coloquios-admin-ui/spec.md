## ADDED Requirements

### Requirement: Crear convocatoria de coloquio

El sistema SHALL permitir crear una convocatoria especificando materia, cohorte, instancia, días disponibles y cupo por día.

#### Scenario: Crear convocatoria

- **WHEN** el COORDINADOR completa el formulario de convocatoria
- **THEN** el sistema llama a `POST /api/coloquios`
- **AND** muestra la convocatoria creada

### Requirement: Importar alumnos a convocatoria

El sistema SHALL mostrar un formulario para importar alumnos a una convocatoria existente.

### Requirement: Panel de métricas de coloquio

El sistema SHALL mostrar métricas de cada convocatoria (total convocados, reservas activas, total reservas, total resultados, cupos libres).

### Requirement: Admin global de coloquios

El sistema SHALL mostrar todas las convocatorias del tenant con métricas agregadas (`GET /api/coloquios/admin`).

### Requirement: Gestión de resultados

El sistema SHALL permitir cargar resultados (nota_final) para los alumnos de una convocatoria.
