## MODIFIED Requirements

### Requirement: Sidebar con secciones Admin y Finanzas

El sidebar SHALL agrupar:
- **Administración**
  - Carreras → `/admin/carreras` (permiso `estructura:gestionar`)
  - Cohortes → `/admin/cohortes`
  - Materias → `/admin/materias`
  - Usuarios → `/admin/usuarios` (permiso `usuarios:gestionar`)
  - Auditoría → `/admin/auditoria` (permiso `auditoria:ver`)
- **Finanzas**
  - Liquidaciones → `/liquidaciones` (permiso `liquidaciones:ver`)
  - Facturas → `/facturas`
  - Grilla Salarial → `/liquidaciones/grilla`
  - KPIs → `/liquidaciones/kpis`
