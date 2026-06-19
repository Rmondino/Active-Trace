## Why

Último change del proyecto. Crea las pantallas de administración que faltan: estructura académica (carreras, cohortes, materias), usuarios del tenant, panel de auditoría con filtros. Las pantallas de finanzas (liquidaciones, facturas, grilla salarial) ya existen de C-18. C-24 las integra todas en un solo lugar con navegación completa.

## What Changes

- **Admin Estructura**: páginas ABM de carreras, cohortes, materias
- **Admin Usuarios**: página ABM de usuarios con PII enmascarado en listado
- **Admin Auditoría**: log de auditoría con filtros (acción, materia, actor, fechas)
- **Dashboard Finanzas**: integrar páginas existentes de liquidaciones, facturas, grilla salarial, KPIs
- **Sidebar**: agrupar Admin y Finanzas con sus sub-ítems

## Capabilities

### New Capabilities
- `admin-estructura-ui`: ABM carreras, cohortes, materias
- `admin-usuarios-ui`: ABM usuarios con PII masking
- `admin-auditoria-ui`: Log de auditoría con filtros

### Modified Capabilities
- `app-layout`: Agregar secciones Admin y Finanzas al sidebar
- `frontend-shell`: Agregar rutas admin

## Impact

- Frontend nuevo: features/admin/ pages
- Frontend modificado: App.tsx, Sidebar.tsx
- Ya existe: features/liquidaciones/ + features/facturas/ (C-18)
