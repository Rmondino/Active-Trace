## Why

Los equipos docentes necesitan asignarse tareas internas con trazabilidad: quién asigna, quién recibe, estado y comentarios. Sin esto, la coordinación queda en canales externos (WhatsApp, email) sin registro.

## What Changes

### Modelos (2 nuevos)
- **Tarea**: asignado_a, asignado_por, materia (nullable), estado (Pendiente/En progreso/Resuelta/Cancelada), descripcion, contexto_id
- **ComentarioTarea**: hilo de comentarios por tarea

### Endpoints
| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| `POST` | `/api/tareas` | Crear/asignar tarea (F8.2) | `tareas:gestionar` |
| `GET` | `/api/tareas` | Admin: todas con filtros (F8.3) | `tareas:gestionar` |
| `GET` | `/api/tareas/mias` | Mis tareas asignadas (F8.1) | autenticado |
| `GET` | `/api/tareas/{id}` | Detalle + comentarios | autenticado (si involucrado) |
| `PATCH` | `/api/tareas/{id}/estado` | Cambiar estado | autenticado (asignado o admin) |
| `POST` | `/api/tareas/{id}/comentarios` | Agregar comentario | autenticado (si involucrado) |

### State machine
Pendiente → En progreso → Resuelta | Cancelada (desde cualquier estado no terminal)

### Migración 012
- `tarea`, `comentario_tarea`
