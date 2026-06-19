## MODIFIED Requirements

### Requirement: Sidebar adaptativo por permisos

El sidebar SHALL mostrar ítems de navegación filtrados según los permisos del usuario. Cada ítem tiene un `requiredPermission` opcional; si el usuario no tiene ese permiso, el ítem no se renderiza. Los ítems base son:
- Dashboard (home) — todos los usuarios autenticados
- 2FA Setup — usuarios sin 2FA activo
- **Mis Comisiones** (`/comision`) — usuarios con permiso `calificaciones:ver`

#### Scenario: Sidebar filtra ítems por permisos (incluyendo comisiones)

- **WHEN** un usuario autenticado con permiso `calificaciones:ver` ve el sidebar
- **THEN** se muestran los ítems base más "Mis Comisiones"
- **AND** los ítems cuyo `requiredPermission` (si existe) está en los permisos del usuario
