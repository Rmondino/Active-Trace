## ADDED Requirements

### Requirement: Monitor general con filtros

El sistema SHALL mostrar el monitor académico general con filtros por materia, regional, comisión, búsqueda de alumno, actividad y estado (atrasado/no_atrasado). SHALL usar `scope=general` para mostrar datos de todas las comisiones (requiere COORDINADOR/ADMIN).

#### Scenario: Monitor general con filtros

- **WHEN** el COORDINADOR navega al monitor con `scope=general`
- **THEN** se muestra la tabla de alumnos de todas las comisiones con filtros aplicables

#### Scenario: Monitor filtrado por estado

- **WHEN** el COORDINADOR selecciona el filtro "atrasado"
- **THEN** solo se muestran los alumnos atrasados
