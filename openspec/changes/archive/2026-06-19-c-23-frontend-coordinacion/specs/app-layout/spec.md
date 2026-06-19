## MODIFIED Requirements

### Requirement: Sidebar adaptativo por permisos

El sidebar SHALL mostrar ítems de navegación filtrados según los permisos del usuario. Los ítems base son:
- Dashboard (home) — todos los usuarios autenticados
- 2FA Setup — usuarios sin 2FA activo
- Mis Comisiones (`/comision`) — usuarios con permiso `calificaciones:ver`
- **Equipos Docentes** (`/coordinacion/equipos`) — usuarios con permiso `equipos:asignar`
- **Encuentros** (`/coordinacion/encuentros`) — usuarios con permiso `encuentros:gestionar`
- **Coloquios** (`/coordinacion/coloquios`) — usuarios con permiso `coloquios:gestionar`
- **Avisos** (`/coordinacion/avisos`) — usuarios con permiso `avisos:publicar`
- **Tareas** (`/coordinacion/tareas`) — usuarios con permiso `tareas:gestionar`
- **Monitor** (`/coordinacion/monitor`) — usuarios con permiso `atrasados:ver`

#### Scenario: Sidebar con ítems de coordinación

- **WHEN** un usuario autenticado con permisos de coordinación ve el sidebar
- **THEN** se muestran los ítems de equipos, encuentros, coloquios, avisos, tareas y monitor
