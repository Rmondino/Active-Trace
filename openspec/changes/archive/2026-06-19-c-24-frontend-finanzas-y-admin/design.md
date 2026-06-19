## Context

C-24 es el último change. 100% frontend. Backend completo. Las páginas de finanzas ya existen de C-18. Se crean las páginas admin y auditoría.

## Decisions

### D1: Admin agrupado bajo /admin/
- /admin/carreras, /admin/cohortes, /admin/materias, /admin/usuarios, /admin/auditoria
- Layout común con sidebar secundario

### D2: Tablas con TanStack Table
- CRUD tables con sorting para carreras, cohortes, materias, usuarios

### D3: Auditoría con filtros
- Selectores de acción, materia, actor + rango de fechas
- Tabla de resultados con TanStack Table

## File Structure
```
features/admin/
├── pages/
│   ├── CarrerasPage.tsx
│   ├── CohortesPage.tsx
│   ├── MateriasPage.tsx
│   ├── UsuariosPage.tsx
│   └── AuditoriaPage.tsx
├── services/
│   ├── estructuraService.ts
│   ├── usuariosService.ts
│   └── auditoriaService.ts
├── hooks/
│   ├── useCarreras.ts
│   ├── useCohortes.ts
│   ├── useMaterias.ts
│   ├── useUsuarios.ts
│   └── useAuditoria.ts
└── types/
    ├── estructura.ts
    ├── usuarios.ts
    └── auditoria.ts
```
