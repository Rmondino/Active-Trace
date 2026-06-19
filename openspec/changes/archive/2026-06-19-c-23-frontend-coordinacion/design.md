## Context

C-22 implementó la feature de comisión del PROFESOR. C-23 completa el frontend de coordinación con 6 módulos: equipos docentes, encuentros/guardias, coloquios, avisos, tareas y monitor transversal. El backend tiene todos los endpoints (C-08, C-13, C-14, C-15, C-16, C-11). No se necesita ningún cambio backend.

## Goals / Non-Goals

**Goals:**
- Gestión de equipos docentes: listado, asignación masiva, clonar, vigencia, export
- Gestión de encuentros: CRUD slots + instancias + contenido aula + vista admin
- Gestión de guardias: listado global y export
- Gestión de coloquios: convocatorias, alumnos, resultados, admin global
- Gestión de avisos: ABM completo con alcance, severidad, vigencia, ack
- Gestión de tareas: mis tareas, asignar, comentarios, admin global
- Monitor transversal: vista general con filtros

**Non-Goals:**
- No se toca backend
- No se implementa edición de slots de encuentro (solo creación y edición de instancias)
- No se implementa gestión de cupos de coloquio (read-only)

## Decisions

### D1: Páginas independientes por feature
- **Decisión**: Cada feature es una página independiente bajo `/coordinacion/{feature}`, no tabs
- **Por qué**: Son módulos conceptualmente distintos. Tabs solo si están muy relacionados (ej: encuentros y guardias podrían compartir layout)
- **Implementación**: `CoordinacionLayout` genérico con sidebar secundario de navegación entre features, o páginas independientes

**Actualización**: Páginas independientes sin layout compartido entre features. Cada feature tiene su propia page.

### D2: Equipos con tabs internas
- **Decisión**: La página de equipos tiene tabs internas: Asignaciones, Asignación Masiva, Clonar, Vigencia
- **Por qué**: Son operaciones sobre la misma entidad (asignaciones). Las tabs evitan cambiar de página.

### D3: TanStack Table para tablas con filtros
- **Decisión**: TanStack Table con sorting client-side para todas las tablas (asignaciones, tareas, avisos, monitores)
- **Por qué**: Ya está en el stack, reutilizado de C-22.

### D4: Formularios modales para creación
- **Decisión**: Usar modales para formularios de creación (nuevo aviso, nueva tarea, nuevo slot, nueva guardia, asignación masiva)
- **Por qué**: Evita navegación, mantiene contexto de la lista.

## File Structure

```
frontend/src/features/coordinacion/
├── pages/
│   ├── EquiposPage.tsx             ← Tabs: Asignaciones, Masiva, Clonar, Vigencia
│   ├── EncuentrosPage.tsx          ← Slots + instancias + contenido aula
│   ├── GuardiasPage.tsx            ← Listado global + export
│   ├── ColoquiosPage.tsx           ← Admin global de convocatorias
│   ├── AvisosPage.tsx              ← ABM avisos
│   ├── TareasPage.tsx              ← Admin global de tareas
│   └── MonitorPage.tsx             ← Monitor transversal con filtros
├── components/
│   ├── equipos/
│   │   ├── AsignacionesTable.tsx
│   │   ├── AsignacionMasivaForm.tsx
│   │   ├── ClonarEquipoForm.tsx
│   │   └── VigenciaForm.tsx
│   ├── encuentros/
│   │   ├── SlotForm.tsx
│   │   ├── InstanciasTable.tsx
│   │   └── InstanciaEditModal.tsx
│   ├── guardias/
│   │   └── GuardiasTable.tsx
│   ├── coloquios/
│   │   ├── ConvocatoriaCard.tsx
│   │   ├── ConvocatoriaForm.tsx
│   │   └── ResultadosForm.tsx
│   ├── avisos/
│   │   ├── AvisoForm.tsx
│   │   └── AvisosTable.tsx
│   ├── tareas/
│   │   ├── TareaForm.tsx
│   │   ├── TareasTable.tsx
│   │   └── TareaDetail.tsx
│   └── monitor/
│       └── MonitorTable.tsx
├── hooks/
│   ├── useEquipos.ts
│   ├── useEncuentros.ts
│   ├── useGuardias.ts
│   ├── useColoquios.ts
│   ├── useAvisos.ts
│   ├── useTareas.ts
│   └── useMonitor.ts
├── services/
│   ├── equiposService.ts
│   ├── encuentrosService.ts
│   ├── guardiasService.ts
│   ├── coloquiosService.ts
│   ├── avisosService.ts
│   ├── tareasService.ts
│   └── monitorService.ts
└── types/
    ├── equipos.ts
    ├── encuentros.ts
    ├── guardias.ts
    ├── coloquios.ts
    ├── avisos.ts
    ├── tareas.ts
    └── monitor.ts
```
