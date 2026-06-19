## ADDED Requirements

### Requirement: Protección de rutas por autenticación

El sistema SHALL tener un componente `ProtectedRoute` que verifique que el usuario está autenticado antes de renderizar el contenido de la ruta. Si no hay sesión activa, SHALL redirigir a `/login` preservando la URL original como `?redirect=` para redirigir de vuelta después del login.

#### Scenario: Usuario autenticado accede a ruta protegida

- **WHEN** un usuario con sesión activa navega a una ruta protegida
- **THEN** el componente renderiza el contenido de la ruta

#### Scenario: Usuario no autenticado redirigido a login

- **WHEN** un usuario sin sesión navega a una ruta protegida
- **THEN** el componente redirige a `/login?redirect=<url_original>`

### Requirement: Protección de rutas por permiso

El componente `ProtectedRoute` SHALL aceptar un prop opcional `requiredPermission` de tipo `string` (formato `modulo:accion`). Cuando se especifica, SHALL verificar que el usuario tenga ese permiso. Si no lo tiene, SHALL mostrar un mensaje de "acceso denegado" (HTTP 403) o redirigir al dashboard según el caso.

#### Scenario: Usuario con permiso accede

- **WHEN** un usuario autenticado con permiso `modulo:accion` navega a una ruta que requiere ese permiso
- **THEN** el componente renderiza el contenido de la ruta

#### Scenario: Usuario sin permiso ve acceso denegado

- **WHEN** un usuario autenticado pero sin permiso `modulo:accion` navega a una ruta que lo requiere
- **THEN** el componente muestra un mensaje de "No tienes permiso para acceder a esta sección"
