## Why

Tenemos el modelo `Asignacion` desde C-07, pero solo su CRUD básico. El usuario necesita herramientas de gestión de equipos docentes: ver mis asignaciones, asignar en bloque, clonar entre períodos, ajustar vigencias y exportar. Sin esto, armar el equipo cada cuatrimestre es tedioso y propenso a errores.

## What Changes

### Endpoints sobre Asignacion (sin nuevos modelos)

| Funcionalidad | Endpoint | Descripción |
|--------------|----------|-------------|
| **F4.2** Mis equipos | `GET /api/equipos/mis-equipos` | Asignaciones del usuario logueado con contexto completo |
| **F4.3** Gestión asignaciones | `GET /api/equipos/asignaciones` | Vista filtrable de todas las asignaciones del tenant |
| **F4.4** Asignación masiva | `POST /api/equipos/asignaciones/masiva` | Bloque docentes × materia × carrera × cohorte × rol |
| **F4.5** Clonar equipo | `POST /api/equipos/clonar` | Duplica asignaciones entre cohortes (RN-12) |
| **F4.6** Vigencia general | `PATCH /api/equipos/vigencia` | Actualiza desde/hasta de todo un equipo |
| **F4.7** Exportar equipo | `GET /api/equipos/export` | Archivo xlsx descargable |

### Permisos
- `equipos:asignar` — para todas las operaciones (COORDINADOR, ADMIN)
- Mis equipos: cualquier usuario logueado ve sus propias asignaciones

### Auditoría
- `ASIGNACION_MODIFICAR` en asignación masiva, clonado y cambio de vigencia

### Dependencias
- Ninguna nueva — reusa openpyxl para export
- Sin migración — opera sobre Asignacion existente
