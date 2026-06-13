## ADDED Requirements

### Requirement: Rate limiting en login

El sistema SHALL limitar los intentos de login a 5 requests por ventana de 60 segundos, combinando la IP de origen y el email destino.

#### Scenario: Límite no alcanzado

- **WHEN** un cliente envía 4 requests de login en 60 segundos
- **THEN** todos los requests se procesan normalmente

#### Scenario: Límite alcanzado

- **WHEN** un cliente envía 6 o más requests de login en 60 segundos (misma IP y mismo email)
- **THEN** el sistema responde con HTTP 429 y header `Retry-After`

#### Scenario: Ventana deslizante

- **WHEN** un cliente excede el límite, espera 60 segundos, y vuelve a intentar
- **THEN** el request se procesa normalmente (la ventana se deslizó)

#### Scenario: Distintos emails desde misma IP

- **WHEN** un cliente envía 5 intentos fallidos al email A y luego intenta con email B
- **THEN** el intento con email B se procesa normalmente (el rate limit es por tupla IP+email)
