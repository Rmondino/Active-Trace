## MODIFIED Requirements

### Requirement: Enrutamiento de features académicas

El sistema SHALL incluir las rutas para las features académicas del PROFESOR bajo el layout protegido. Las nuevas rutas SHALL ser:
- `/comision` → `ComisionSelectorPage` (selección de materia/cohorte)
- `/comision/:materiaId/:cohorteId` → `ComisionLayout` con tabs anidadas
  - `calificaciones` → importación + umbral
  - `atrasados` → tabla de atrasados + ranking + reporte
  - `comunicacion` → preview + envío + tracking

#### Scenario: Rutas académicas existen

- **WHEN** un usuario autenticado navega a `/comision`
- **THEN** se renderiza la página de selección de comisión

#### Scenario: Ruta de comisión con tabs

- **WHEN** un usuario autenticado navega a `/comision/:materiaId/:cohorteId/calificaciones`
- **THEN** se renderiza el layout de comisión con la tab de calificaciones activa
