## 1. Frontend — Router + Layout + Sidebar

- [x] 1.1 Agregar servicio `GET /api/calificaciones` en `features/comision/services/calificacionesService.ts`
- [x] 1.2 Agregar rutas de comisión en `App.tsx` (`/comision`, `/comision/:materiaId/:cohorteId/*`)
- [x] 1.3 Agregar item "Mis Comisiones" al sidebar en `layout/Sidebar.tsx`
- [x] 1.4 Crear `features/comision/types/calificaciones.ts` con interfaces de datos
- [x] 1.5 Crear `features/comision/types/analisis.ts` con interfaces de datos
- [x] 1.6 Crear `features/comision/types/comunicaciones.ts` con interfaces de datos

## 2. Frontend — Selector de comisión

- [x] 2.1 Crear `features/comision/services/comisionService.ts` con GET de asignaciones del usuario
- [x] 2.2 Crear hook `useAsignaciones` con TanStack Query
- [x] 2.3 Crear componente `ComisionSelector` con lista de materias+cohortes asignadas
- [x] 2.4 Crear `ComisionSelectorPage` con buscador y selección

## 3. Frontend — Layout de comisión con tabs

- [x] 3.1 Crear `ComisionLayout` con tabs (Calificaciones, Atrasados, Comunicación) usando nested routes
- [x] 3.2 Crear `ComisionContext` o leer materia_id/cohorte_id de URL params

## 4. Frontend — Importación de calificaciones

- [x] 4.1 Crear `features/comision/services/calificacionesService.ts` con endpoints de import, preview, confirm, completions
- [x] 4.2 Crear hook `useImportCalificaciones` con mutation para upload + preview
- [x] 4.3 Crear hook `useConfirmImport` con mutation para confirmar importación
- [x] 4.4 Crear hook `useImportCompletions` con mutation para completions
- [x] 4.5 Crear componente `FileUpload` con input file y preview de columnas
- [x] 4.6 Crear componente `ActividadesSelector` con checkboxes de actividades
- [x] 4.7 Crear `CalificacionesPage` integrando upload, preview, selector y confirmación

## 5. Frontend — Configuración de umbral

- [x] 5.1 Crear `features/comision/services/umbralService.ts` con GET y PUT
- [x] 5.2 Crear hook `useUmbral` con query + mutation
- [x] 5.3 Crear componente `UmbralConfig` con slider y valores aprobatorios
- [x] 5.4 Integrar `UmbralConfig` en `CalificacionesPage`

## 6. Frontend — Análisis de atrasados

- [x] 6.1 Crear `features/comision/services/analisisService.ts` con endpoints de atrasados, ranking, reporte, notas-finales, export
- [x] 6.2 Crear hook `useAtrasados` con query
- [x] 6.3 Crear hook `useRanking` con query
- [x] 6.4 Crear hook `useReporte` con query
- [x] 6.5 Crear hook `useNotasFinales` con query
- [x] 6.6 Crear `AtrasadosTable` con TanStack Table (sorting, row selection, causas coloreadas)
- [x] 6.7 Crear `RankingTable` con TanStack Table
- [x] 6.8 Crear `ReporteResumen` con cards de métricas
- [x] 6.9 Crear `NotasFinalesTable` con columnas dinámicas por actividad
- [x] 6.10 Crear `AtrasadosPage` integrando tabla, ranking, reporte, notas y export

## 7. Frontend — Comunicación a atrasados

- [x] 7.1 Crear `features/comision/services/comunicacionesService.ts` con endpoints de preview, enviar, tracking
- [x] 7.2 Crear hook `usePreviewComunicacion` con mutation
- [x] 7.3 Crear hook `useEnviarComunicacion` con mutation
- [x] 7.4 Crear hook `useTrackingComunicaciones` con query
- [x] 7.5 Crear `ComunicacionForm` con inputs de asunto/cuerpo + placeholders
- [x] 7.6 Crear `ComunicacionPreview` con preview renderizado por alumno
- [x] 7.7 Crear `TrackingTable` con estados coloreados
- [x] 7.8 Crear `ComunicacionPage` integrando form, preview, envío y tracking

## 8. Tests

- [x] 8.1 Test: ComisionSelector render y muestra lista de asignaciones
- [x] 8.2 Test: FileUpload render y validación de archivo
- [x] 8.3 Test: AtrasadosTable render con datos mockeados
- [x] 8.4 Test: ComunicacionForm render y validación de placeholders
- [x] 8.5 Test: ComunicacionPreview muestra preview por alumno
- [x] 8.6 Test: TrackingTable muestra estados con colores
