## ADDED Requirements

### Requirement: Cliente Axios centralizado

El frontend SHALL tener un cliente Axios centralizado en `src/shared/services/api.ts` con una instancia preconfigurada con `baseURL` desde variable de entorno `VITE_API_URL` (default `http://localhost:8000`). Todos los módulos del frontend SHALL importar esta instancia para hacer peticiones HTTP.

#### Scenario: La instancia se crea con la URL base

- **WHEN** se importa la instancia de `api.ts`
- **THEN** tiene `baseURL` configurada desde `VITE_API_URL` o el valor por defecto

### Requirement: Interceptor de auth (Authorization header)

El interceptor de request SHALL agregar automáticamente el header `Authorization: Bearer <access_token>` cuando exista un token en el estado de sesión.

#### Scenario: Agrega token a las peticiones

- **WHEN** hay un `access_token` en el estado de auth
- **THEN** el interceptor agrega `Authorization: Bearer <token>` al header de la request

### Requirement: Refresh transparente de tokens

El interceptor de response SHALL interceptar errores HTTP 401 y, si existe un `refresh_token`, intentar renovar el access token mediante `POST /api/auth/refresh`. Si el refresh es exitoso, SHALL reenviar la petición original con el nuevo token. Si el refresh falla, SHALL redirigir al login.

#### Scenario: Refresh exitoso con cola de peticiones

- **WHEN** una petición recibe 401 y hay refresh token disponible
- **THEN** el interceptor llama a `/api/auth/refresh`, actualiza los tokens en el estado de sesión, y reenvía la petición original
- **AND** si múltiples peticiones reciben 401 simultáneamente, solo una realiza el refresh y las demás se encolan hasta que el refresh se complete

#### Scenario: Refresh fallido redirige a login

- **WHEN** una petición recibe 401 y el refresh token es inválido o expiró
- **THEN** el interceptor limpia el estado de sesión y redirige a `/login`
