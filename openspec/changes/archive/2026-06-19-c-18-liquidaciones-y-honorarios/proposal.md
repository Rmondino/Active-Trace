## Why

El módulo de liquidaciones es el corazón financiero del sistema. FINANZAS necesita calcular y gestionar los honorarios de todos los docentes por período: salario base por rol, plus por grupo de materias, liquidación de facturas de docentes monotributistas, y KPIs contables. Es el último módulo de backend importante del proyecto.

## What Changes

**Modelos:**
- `SalarioBase`: monto fijo por rol con vigencia
- `SalarioPlus`: plus por (grupo × rol) con vigencia y tope de acumulación
- `MateriaGrupoPlus`: mapeo materia → grupo con vigencia (PA-22)
- `Liquidacion`: período, base + plus = total, estado Abierta/Cerrada
- `Factura`: documento de cobro de docentes facturantes

**Endpoints:**
- `/api/salarios/bases` — CRUD SalarioBase (guard `liquidaciones:configurar-salarios`)
- `/api/salarios/plus` — CRUD SalarioPlus
- `/api/salarios/grupos-materia` — CRUD MateriaGrupoPlus
- `/api/liquidaciones` — generar, listar, ver detalle, cerrar
- `/api/liquidaciones/kpis` — KPIs contables
- `/api/facturas` — CRUD Facturas

**Frontend:**
- Grilla salarial (bases + plus + grupos)
- Liquidaciones (generar, listar, detalle, cerrar)
- Facturas (listar, subir, abonar)
- KPIs contables

## Capabilities

### New Capabilities
- `grilla-salarial`: ABM salario base, plus, grupos materia
- `liquidaciones-calculo`: Generar, listar, cerrar liquidaciones
- `facturas-gestion`: CRUD facturas de docentes facturantes
- `kpis-contables`: KPIs con separación factura/no-factura

### Modified Capabilities
- `app-layout`: Agregar items Liquidaciones y Facturas
- `frontend-shell`: Agregar rutas

## Impact

- Backend: 5 modelos, 5 repos, 1 service, 3 routers, migration
- Frontend: features/liquidaciones/ y features/facturas/
