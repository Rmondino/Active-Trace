## Why

C-22 cubrió el flujo del PROFESOR (importar calificaciones, ver atrasados, comunicarse). C-23 cubre el flujo del COORDINADOR/ADMIN: la gestión estructural del cuatrimestre. El COORDINADOR necesita asignar docentes a materias (equipos), crear encuentros y guardias, gestionar coloquios, publicar avisos, asignar tareas internas, y monitorear el estado académico transversal de todas las comisiones. Sin esto, el rol de coordinación no tiene herramientas en el frontend.

## What Changes

- **Nuevo feature**: `coordinacion/` — módulo de gestión del COORDINADOR/ADMIN
- **Equipos docentes**: listar asignaciones, asignación masiva, clonar entre cohortes, modificar vigencia, exportar XLSX
- **Encuentros**: CRUD de slots, crear encuentros recurrentes/únicos, editar instancias, contenido para aula virtual, vista admin
- **Guardias**: registro y consulta global, export XLSX
- **Coloquios**: crear convocatorias, importar alumnos, ver reservas, cargar resultados, admin global
- **Avisos**: ABM completo con alcance (Global/PorMateria/PorCohorte/PorRol), severidad, vigencia, ack tracking
- **Tareas internas**: mis tareas, asignar/delegar, comentarios, cambio de estado, admin con filtros
- **Monitor transversal**: vista general con filtros (materia, regional, comisión, estado, búsqueda)

## Capabilities

### New Capabilities
- `equipos-gestion-ui`: Listado de asignaciones, asignación masiva, clonar, vigencia, export
- `encuentros-admin-ui`: CRUD slots, instancias, contenido aula, vista admin
- `guardias-admin-ui`: Registro y consulta global de guardias
- `coloquios-admin-ui`: Convocatorias, alumnos, reservas, resultados, admin global
- `avisos-gestion-ui`: ABM avisos con alcance, severidad, vigencia, ack
- `tareas-gestion-ui`: Asignar, comentarios, estados, admin con filtros
- `monitor-transversal-ui`: Monitor general con filtros académicos

### Modified Capabilities
- `app-layout`: Agregar items de navegación de coordinación al sidebar
- `frontend-shell`: Agregar rutas de coordinación al router

## Impact

- **Nuevo directorio**: `frontend/src/features/coordinacion/` con toda la feature
- **Modificaciones**: `frontend/src/App.tsx` (nuevas rutas), `frontend/src/layout/Sidebar.tsx` (nuevos items de menú)
- **Dependencias**: TanStack Table para tablas (ya instalado)
