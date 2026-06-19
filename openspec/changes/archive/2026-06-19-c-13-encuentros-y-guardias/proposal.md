## Why

Los docentes necesitan gestionar encuentros sincrónicos (clases virtuales) con sus comisiones: crear slots recurrentes o encuentros únicos, editar instancias, y generar contenido para publicar en el aula virtual del LMS. También necesitan registrar guardias de atención a alumnos. Sin esto, la coordinación de horarios y el registro de guardias queda fuera del sistema.

## What Changes

### Modelos (3 nuevos)

| Modelo | Descripción |
|--------|-------------|
| **SlotEncuentro** | Plantilla de recurrencia semanal o encuentro único |
| **InstanciaEncuentro** | Encuentro concreto derivado de un slot o independiente |
| **Guardia** | Registro de guardia de atención |

### Endpoints

| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| `POST` | `/api/encuentros/slots` | Crear slot (recurrente o único, RN-13) | `encuentros:gestionar` |
| `GET` | `/api/encuentros/slots?materia_id=X` | Listar slots | `encuentros:gestionar` |
| `GET` | `/api/encuentros/slots/{id}` | Detalle slot + instancias | `encuentros:gestionar` |
| `PATCH` | `/api/encuentros/instancias/{id}` | Editar instancia (F6.3) | `encuentros:gestionar` |
| `GET` | `/api/encuentros/instancias?materia_id=X` | Listar instancias | `encuentros:gestionar` |
| `GET` | `/api/encuentros/contenido-aula?materia_id=X` | Bloque HTML (F6.4) | `encuentros:gestionar` |
| `GET` | `/api/encuentros/vista-admin` | Vista transversal (F6.5) | `encuentros:gestionar` (scope admin) |
| `POST` | `/api/guardias` | Registrar guardia (F6.6) | `encuentros:gestionar` |
| `GET` | `/api/guardias?materia_id=X` | Consultar guardias | `encuentros:gestionar` |
| `GET` | `/api/guardias/export?materia_id=X` | Exportar guardias | `encuentros:gestionar` |

### Migración 009
- `slot_encuentro`, `instancia_encuentro`, `guardia`
