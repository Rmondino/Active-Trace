## ADDED Requirements

### Requirement: CRUD de slots de encuentro

El sistema SHALL permitir crear slots de encuentro (recurrentes o únicos), listarlos por materia, ver detalle con instancias, y editar campos.

#### Scenario: Crear slot recurrente

- **WHEN** el COORDINADOR completa el formulario con título, hora, día_semana, fecha_inicio, cant_semanas, vigencia
- **THEN** el sistema llama a `POST /api/encuentros/slots`
- **AND** muestra el slot creado con sus instancias generadas

#### Scenario: Crear slot único

- **WHEN** el COORDINADOR completa el formulario con título, hora, fecha_unica, vigencia
- **THEN** el sistema crea un slot sin recurrencia

### Requirement: Editar instancia de encuentro

El sistema SHALL permitir editar el estado, meet_url, video_url y comentario de cada instancia individual.

#### Scenario: Editar instancia

- **WHEN** el COORDINADOR edita una instancia y guarda
- **THEN** el sistema llama a `PATCH /api/encuentros/instancias/{id}`

### Requirement: Vista admin de encuentros

El sistema SHALL mostrar una vista consolidada de todos los encuentros (slots + instancias) con filtro por materia.

### Requirement: Contenido para aula virtual

El sistema SHALL proveer un botón "Generar HTML aula" que obtenga el contenido HTML y lo copie al portapapeles.
