## Context

C-21 creó el shell del frontend (login, layout, route guard, HTTP client). El backend tiene todos los endpoints necesarios (C-10 calificaciones, C-11 análisis, C-12 comunicaciones). C-22 es la primera feature real: permite al PROFESOR gestionar su comisión de principio a fin: importar calificaciones → configurar umbral → ver atrasados → comunicarse con ellos.

Los endpoints del backend ya fueron explorados y están completos. No se necesita ningún cambio backend.

## Goals / Non-Goals

**Goals:**
- Selector de materia/cohorte para que el PROFESOR elija qué comisión gestionar
- Upload de archivo CSV/XLSX con preview de actividades detectadas y selector de columnas
- Confirmación de importación con selección de actividades
- Configuración visual del umbral de aprobación (slider + valores textuales)
- Tabla de alumnos atrasados con causas (faltantes / baja nota), ranking, reporte rápido
- Vista de notas finales consolidadas por alumno
- Comunicación a atrasados: seleccionar alumnos, preview con templates, envío, tracking de estado
- Exportación de entregas sin corregir (XLSX)
- Sidebar actualizado con items de navegación para las nuevas features

**Non-Goals:**
- No se toca el backend
- No se implementa aprobación de comunicaciones (es flujo de COORDINADOR, C-23)
- No se implementa monitor general ni filtros avanzados (scope general)
- No se implementa multi-selección compleja en tabla de atrasados

## Decisions

### D1: Selector de comisión como pantalla de inicio post-login
- **Decisión**: La ruta `/` (dashboard) redirige al selector de comisión para PROFESOR, o al dashboard general para otros roles.
- **Por qué**: El PROFESOR necesita elegir qué materia+cohorte gestionar. Es el entry point natural.
- **Implementación**: Componente `ComisionSelector` que lista las asignaciones activas del usuario con filtro de búsqueda.

### D2: Vista de tabs dentro de la comisión
- **Decisión**: Una vez seleccionada comisión, se usan tabs (react-router nested routes) para: Calificaciones, Atrasados, Comunicación.
- **Por qué**: Son las 3 operaciones principales del flujo FL-02. Tabs permiten navegar sin perder el contexto de la comisión seleccionada.
- **Rutas**: `/comision/:materiaId/:cohorteId/calificaciones`, `/comision/:materiaId/:cohorteId/atrasados`, `/comision/:materiaId/:cohorteId/comunicacion`

### D3: TanStack Table para tablas de datos
- **Decisión**: Usar `@tanstack/react-table` para la tabla de atrasados y notas finales
- **Por qué**: Ya está en las skills del proyecto. Provee sorting, filtering, y selección de filas out of the box. La tabla de atrasados necesita sorting por columna y selección de alumnos para comunicación.
- **Implementación**: Columnas tipadas con `createColumnHelper`, sorting client-side, row selection para marcar destinatarios de comunicación.

### D4: File upload con preview sin librería externa
- **Decisión**: Usar `<input type="file">` nativo con lectura del nombre y tamaño, más una vista previa de las columnas detectadas que devuelve el backend.
- **Por qué**: El backend procesa el archivo y devuelve el preview. El frontend solo necesita subir el archivo y mostrar el resultado. No se necesita librería de upload.
- **Importante**: El preview se obtiene del response de `POST /api/calificaciones/import` con `confirm=false`.

### D5: Comunicación con selección desde tabla de atrasados
- **Decisión**: Los alumnos atrasados se muestran en una tabla TanStack con checkboxes de selección. Al hacer clic en "Comunicar", los alumnos seleccionados pasan al paso de preview → envío.
- **Por qué**: El usuario selecciona los atrasados que quiere contactar, ve el preview, y confirma el envío. Flujo natural.
- **Implementación**: 3 pasos: (1) seleccionar alumnos en tabla, (2) escribir template y ver preview, (3) confirmar envío y ver tracking.

### D6: Template de comunicación con placeholders
- **Decisión**: Inputs de texto para asunto y cuerpo con placeholders `{alumno_nombre}`, `{alumno_apellidos}`, `{materia}`, `{comision}`. El backend los renderiza.
- **Por qué**: El backend ya soporta templates con estas variables. El frontend solo envía el template y muestra el preview renderizado.

### D7: Estado compartido de comisión via React Context
- **Decisión**: `ComisionContext` con la materia_id y cohorte_id seleccionadas, disponible para todas las tabs hijas.
- **Por qué**: Todas las vistas (calificaciones, atrasados, comunicación) necesitan materia_id y cohorte_id. Evita pasarlos por props.
- **Alternativa**: Sacarlos de la URL (react-router params) — alcanza, no necesita contexto global.

**Actualización**: Usar URL params directamente (`useParams`) en lugar de contexto. Es más simple, ya que react-router provee los params. Solo se necesita contexto si el estado es compartido entre tabs hermanos.

### D8: Servicios feature-specific con TanStack Query
- **Decisión**: Crear hooks de query/mutation específicos para cada feature (calificaciones, análisis, comunicaciones) usando TanStack Query.
- **Por qué**: Separa concerns, permite caching, refetch automático.
- **Implementación**: `features/comision/hooks/useCalificaciones.ts`, `useAnalisis.ts`, `useComunicaciones.ts`

## Frontend File Structure

```
frontend/src/features/comision/
├── pages/
│   ├── ComisionSelectorPage.tsx    ← Selector de materia/cohorte
│   ├── ComisionLayout.tsx          ← Layout con tabs (calificaciones/atrasados/comunicacion)
│   ├── CalificacionesPage.tsx      ← Import + preview + confirm + umbral
│   ├── AtrasadosPage.tsx           ← Tabla atrasados + ranking + reporte
│   └── ComunicacionPage.tsx        ← Preview + envío + tracking
├── components/
│   ├── ComisionSelector.tsx
│   ├── FileUpload.tsx              ← Upload con preview de columnas
│   ├── ActividadesSelector.tsx     ← Checkboxes de actividades detectadas
│   ├── UmbralConfig.tsx            ← Slider + valores aprobatorios
│   ├── AtrasadosTable.tsx          ← TanStack Table con sorting/selection
│   ├── RankingTable.tsx            ← Ranking de aprobados
│   ├── ReporteResumen.tsx          ← Reporte rápido card
│   ├── NotasFinalesTable.tsx       ← Notas consolidadas
│   ├── ComunicacionForm.tsx        ← Template inputs + preview
│   ├── ComunicacionPreview.tsx     ← Preview renderizado por alumno
│   └── TrackingTable.tsx           ← Estado de comunicaciones enviadas
├── hooks/
│   ├── useCalificaciones.ts        ← Mutations: import, confirm, completions; Query: list
│   ├── useUmbral.ts                ← Query + Mutation: get/put umbral
│   ├── useAnalisis.ts              ← Queries: atrasados, ranking, reporte, notas, monitor
│   └── useComunicaciones.ts        ← Mutations: preview, enviar; Query: tracking
├── services/
│   ├── calificacionesService.ts    ← Llamadas a API de calificaciones
│   ├── umbralService.ts
│   ├── analisisService.ts
│   └── comunicacionesService.ts
└── types/
    ├── calificaciones.ts
    ├── analisis.ts
    └── comunicaciones.ts
```

## Flujo de navegación

```
/login → / (ComisionSelectorPage)
           │
           ▼
/comision/:materiaId/:cohorteId
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
Califs  Atrasados  Comunic
(tab 1) (tab 2)   (tab 3)
```

## Risks / Trade-offs

**[Risk 1] Preview en memoria del backend se pierde al reiniciar**
→ **Mitigación**: El `_previews` está en un dict en memoria. Si el servidor se reinicia, el usuario debe re-subir el archivo. Aceptado.

**[Risk 2] Archivos grandes (muchos alumnos × actividades)**
→ **Mitigación**: El backend procesa en memoria y devuelve preview paginado (muestra). El frontend muestra la muestra + total de alumnos.

**[Risk 3] Comunicación sin aprobación configurable**
→ **Mitigación**: El endpoint `enviar` devuelve `requiere_aprobacion`. Si es true, las comunicaciones quedan Pendiente y el usuario ve el tracking. Si es false, pasan directo a Enviado.

**[Risk 4] Tabla TanStack con datos anidados (notas por alumno × actividad)**
→ **Mitigación**: Usar accessorFn para acceder a valores dentro de objetos anidados. `row.original.actividades[actividadNombre]`.
