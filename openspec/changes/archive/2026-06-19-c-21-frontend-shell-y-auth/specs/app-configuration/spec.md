## ADDED Requirements

### Requirement: CORS configurable

El sistema SHALL incluir middleware CORS en la aplicación FastAPI que permita peticiones desde los orígenes configurados. Los orígenes SHALL ser configurables mediante la variable de entorno `CORS_ORIGINS` (string separado por comas, default `http://localhost:5173,http://localhost:3000`). SHALL soportar credentials (cookies/Authorization header).

#### Scenario: CORS permite origen configurado

- **WHEN** una petición OPTIONS preflight llega desde un origen incluido en `CORS_ORIGINS`
- **THEN** la respuesta incluye `Access-Control-Allow-Origin` con ese origen

#### Scenario: CORS rechaza origen no configurado

- **WHEN** una petición llega desde un origen NO incluido en `CORS_ORIGINS`
- **THEN** la respuesta NO incluye `Access-Control-Allow-Origin`
