## ADDED Requirements

### Requirement: Layout principal con sidebar y header

El sistema SHALL tener un layout principal (`AppLayout`) que incluya un sidebar de navegación a la izquierda y un header superior con información del usuario y botón de logout. El contenido de la ruta se renderiza en el área central mediante `<Outlet />` de react-router.

#### Scenario: Layout se renderiza para rutas autenticadas

- **WHEN** un usuario autenticado navega a cualquier ruta protegida
- **THEN** se renderiza el sidebar, el header y el contenido de la ruta

### Requirement: Sidebar adaptativo por permisos

El sidebar SHALL mostrar ítems de navegación filtrados según los permisos del usuario. Cada ítem tiene un `requiredPermission` opcional; si el usuario no tiene ese permiso, el ítem no se renderiza. Los ítems base son:
- Dashboard (home) — todos los usuarios autenticados
- 2FA Setup — usuarios sin 2FA activo

#### Scenario: Sidebar filtra ítems por permisos

- **WHEN** un usuario autenticado ve el sidebar
- **THEN** solo se muestran los ítems cuyo `requiredPermission` (si existe) está en los permisos del usuario

### Requirement: Header con información del usuario

El header SHALL mostrar el email del usuario autenticado (o nombre si está disponible) y un botón de "Cerrar sesión". En mobile/tablet, el header SHALL incluir un botón hamburguesa para togglear el sidebar.

#### Scenario: Header muestra usuario y logout

- **WHEN** un usuario autenticado ve el header
- **THEN** se muestra su identificador y un botón de "Cerrar sesión"

### Requirement: Sidebar plegable

El sidebar SHALL ser plegable (colapsable a iconos solamente) mediante un botón toggle. El estado del sidebar (plegado/expandido) SHALL persistir durante la sesión.

#### Scenario: Sidebar se pliega

- **WHEN** el usuario hace clic en el botón toggle del sidebar
- **THEN** el sidebar se colapsa mostrando solo iconos
- **AND** al hacer clic de nuevo, se expande mostrando labels
