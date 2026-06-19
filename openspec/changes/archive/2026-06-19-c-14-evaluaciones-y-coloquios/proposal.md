## Why

Los alumnos necesitan rendir coloquios (evaluaciones orales finales). El sistema debe permitir crear convocatorias con días y cupos, que los alumnos reserven turno, y registrar resultados. Sin esto, la gestión de coloquios queda fuera del sistema.

## What Changes

### Modelos (3 nuevos)

| Modelo | Descripción |
|--------|-------------|
| **Evaluacion** | Convocatoria de coloquio (materia, cohorte, instancia, días, cupos) |
| **ReservaEvaluacion** | Turno reservado por un alumno (fecha, hora, estado) |
| **ResultadoEvaluacion** | Nota final del coloquio |

### Endpoints

| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| `POST` | `/api/coloquios` | Crear convocatoria (F7.3) | `coloquios:gestionar` |
| `GET` | `/api/coloquios` | Listar convocatorias (F7.4) | `coloquios:gestionar` / ALUMNO |
| `GET` | `/api/coloquios/{id}` | Detalle + métricas (F7.1) | `coloquios:gestionar` |
| `POST` | `/api/coloquios/{id}/alumnos` | Importar alumnos (F7.2) | `coloquios:gestionar` |
| `POST` | `/api/coloquios/{id}/reservar` | Reservar turno (ALUMNO) | autenticado |
| `GET` | `/api/coloquios/{id}/reservas` | Ver reservas | `coloquios:gestionar` |
| `PATCH` | `/api/coloquios/reservas/{id}` | Cancelar reserva | ALUMNO (propia) |
| `POST` | `/api/coloquios/{id}/resultados` | Registrar nota | `coloquios:gestionar` |
| `GET` | `/api/coloquios/{id}/resultados` | Ver resultados | `coloquios:gestionar` |
| `GET` | `/api/coloquios/admin` | Admin global (F7.5) | `coloquios:gestionar` (admin) |

### Migración 010
- `evaluacion`, `reserva_evaluacion`, `resultado_evaluacion`
