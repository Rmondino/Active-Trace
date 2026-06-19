## MODIFIED Requirements

### Requirement: Enrutamiento de features de coordinación

El sistema SHALL incluir las rutas para las features de COORDINADOR bajo el layout protegido. Las nuevas rutas SHALL ser:
- `/coordinacion/equipos` → gestión de equipos docentes
- `/coordinacion/encuentros` → gestión de encuentros
- `/coordinacion/guardias` → gestión de guardias
- `/coordinacion/coloquios` → gestión de coloquios
- `/coordinacion/avisos` → gestión de avisos
- `/coordinacion/tareas` → gestión de tareas
- `/coordinacion/monitor` → monitor transversal

#### Scenario: Rutas de coordinación existen

- **WHEN** un usuario autenticado navega a `/coordinacion/equipos`
- **THEN** se renderiza la página de gestión de equipos
