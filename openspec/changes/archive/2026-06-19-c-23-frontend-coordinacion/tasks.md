## 1. Router + Sidebar + Shared

- [x] 1.1 Agregar rutas de coordinación en `App.tsx` (equipos, encuentros, guardias, coloquios, avisos, tareas, monitor)
- [x] 1.2 Agregar items de coordinación al sidebar en `Sidebar.tsx`

## 2. Types + Services + Hooks — Equipos

- [x] 2.1 Crear `types/equipos.ts` con interfaces
- [x] 2.2 Crear `services/equiposService.ts` (mis-equipos, asignaciones, masiva, clonar, vigencia, export)
- [x] 2.3 Crear `hooks/useEquipos.ts` con TanStack Query

## 3. Types + Services + Hooks — Encuentros y Guardias

- [x] 3.1 Crear `types/encuentros.ts` con interfaces
- [x] 3.2 Crear `types/guardias.ts` con interfaces
- [x] 3.3 Crear `services/encuentrosService.ts` (slots, instancias, contenido aula, vista admin)
- [x] 3.4 Crear `services/guardiasService.ts` (listar, export)
- [x] 3.5 Crear `hooks/useEncuentros.ts` con TanStack Query
- [x] 3.6 Crear `hooks/useGuardias.ts` con TanStack Query

## 4. Types + Services + Hooks — Coloquios

- [x] 4.1 Crear `types/coloquios.ts` con interfaces
- [x] 4.2 Crear `services/coloquiosService.ts` (CRUD convocatorias, alumnos, resultados, admin)
- [x] 4.3 Crear `hooks/useColoquios.ts` con TanStack Query

## 5. Types + Services + Hooks — Avisos

- [x] 5.1 Crear `types/avisos.ts` con interfaces
- [x] 5.2 Crear `services/avisosService.ts` (ABM, listar, ack, stats)
- [x] 5.3 Crear `hooks/useAvisos.ts` con TanStack Query

## 6. Types + Services + Hooks — Tareas

- [x] 6.1 Crear `types/tareas.ts` con interfaces
- [x] 6.2 Crear `services/tareasService.ts` (mis tareas, crear, estado, comentarios, admin)
- [x] 6.3 Crear `hooks/useTareas.ts` con TanStack Query

## 7. Types + Services + Hooks — Monitor

- [x] 7.1 Crear `types/monitor.ts` con interfaces
- [x] 7.2 Crear `services/monitorService.ts` (monitor general con filtros)
- [x] 7.3 Crear `hooks/useMonitor.ts` con TanStack Query

## 8. UI — Equipos

- [x] 8.1 Crear `components/equipos/AsignacionesTable.tsx` con TanStack Table (sorting, filtros)
- [x] 8.2 Crear `components/equipos/AsignacionMasivaForm.tsx` (multi-select docentes, rol, fechas)
- [x] 8.3 Crear `components/equipos/ClonarEquipoForm.tsx` (origen → destino, fechas)
- [x] 8.4 Crear `components/equipos/VigenciaForm.tsx` (modificar fechas en bloque)
- [x] 8.5 Crear `pages/EquiposPage.tsx` con tabs internas + integración

## 9. UI — Encuentros y Guardias

- [x] 9.1 Crear `components/encuentros/SlotForm.tsx` (recurrente/único, campos de slot)
- [x] 9.2 Crear `components/encuentros/InstanciasTable.tsx` (listado + edición inline)
- [x] 9.3 Crear `components/encuentros/InstanciaEditModal.tsx` (estado, meet_url, video_url, comentario)
- [x] 9.4 Crear `pages/EncuentrosPage.tsx` con integración de slots e instancias
- [x] 9.5 Crear `components/guardias/GuardiasTable.tsx` con export
- [x] 9.6 Crear `pages/GuardiasPage.tsx`

## 10. UI — Coloquios

- [x] 10.1 Crear `components/coloquios/ConvocatoriaForm.tsx` (crear convocatoria)
- [x] 10.2 Crear `components/coloquios/ConvocatoriaCard.tsx` (métricas de convocatoria)
- [x] 10.3 Crear `components/coloquios/ResultadosForm.tsx` (cargar notas)
- [x] 10.4 Crear `pages/ColoquiosPage.tsx` con admin global

## 11. UI — Avisos

- [x] 11.1 Crear `components/avisos/AvisoForm.tsx` (crear/editar con alcance, severidad, vigencia)
- [x] 11.2 Crear `components/avisos/AvisosTable.tsx` (listado con ack count)
- [x] 11.3 Crear `pages/AvisosPage.tsx` con ABM completo

## 12. UI — Tareas

- [x] 12.1 Crear `components/tareas/TareaForm.tsx` (asignar tarea a docente)
- [x] 12.2 Crear `components/tareas/TareasTable.tsx` (admin con filtros)
- [x] 12.3 Crear `components/tareas/TareaDetail.tsx` (estado + comentarios)
- [x] 12.4 Crear `pages/TareasPage.tsx` con admin global

## 13. UI — Monitor

- [x] 13.1 Crear `components/monitor/MonitorTable.tsx` con TanStack Table y filtros
- [x] 13.2 Crear `pages/MonitorPage.tsx` con filtros (materia, regional, comisión, búsqueda, estado)

## 14. Tests

- [x] 14.1 Test: EquiposPage render
- [x] 14.2 Test: AvisosPage ABM flow
- [x] 14.3 Test: TareasPage render y filtros
- [x] 14.4 Test: MonitorPage render con datos
