## ADDED Requirements

### Requirement: Registro de guardias

El sistema SHALL mostrar un formulario para registrar una guardia docente (día, horario, comentarios, materia). La lista de guardias SHALL ser consultable con filtro por materia y exportable a XLSX.

#### Scenario: Listar guardias

- **WHEN** el COORDINADOR navega a la sección de guardias
- **THEN** se muestra una tabla con todas las guardias registradas

#### Scenario: Exportar guardias

- **WHEN** el COORDINADOR hace clic en "Exportar"
- **THEN** se descarga un archivo XLSX con las guardias
