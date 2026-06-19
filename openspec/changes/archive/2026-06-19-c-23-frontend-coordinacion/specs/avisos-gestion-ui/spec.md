## ADDED Requirements

### Requirement: ABM de avisos

El sistema SHALL permitir crear, editar, listar y eliminar avisos. Cada aviso tiene: título, cuerpo, alcance (Global/PorMateria/PorCohorte/PorRol), severidad (Info/Warning/Danger), vigencia (inicio/fin), orden, requiere_ack.

#### Scenario: Crear aviso

- **WHEN** el COORDINADOR completa el formulario de nuevo aviso
- **THEN** el sistema llama a `POST /api/avisos`

#### Scenario: Editar aviso

- **WHEN** el COORDINADOR edita un aviso existente
- **THEN** el sistema llama a `PUT /api/avisos/{id}`

#### Scenario: Eliminar aviso

- **WHEN** el COORDINADOR elimina un aviso
- **THEN** el sistema llama a `DELETE /api/avisos/{id}`

### Requirement: Listado de avisos con métricas

El sistema SHALL listar todos los avisos publicados y para cada uno mostrar el contador de acknowledgments.

### Requirement: Vista de avisos activos para el usuario

El sistema SHALL mostrar los avisos activos filtrados por alcance según el rol y asignaciones del usuario autenticado.

### Requirement: Acknowledgment de aviso

El sistema SHALL permitir al usuario confirmar lectura de un aviso (`POST /api/avisos/{id}/ack`).
