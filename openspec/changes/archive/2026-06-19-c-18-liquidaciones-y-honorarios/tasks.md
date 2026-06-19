## 1. Modelos

- [x] 1.1 Crear `models/salario_base.py` (rol, monto, desde, hasta)
- [x] 1.2 Crear `models/salario_plus.py` (grupo, rol, descripcion, monto, desde, hasta, tope_acumulacion nullable)
- [x] 1.3 Crear `models/materia_grupo_plus.py` (materia_id FK, grupo, desde, hasta)
- [x] 1.4 Crear `models/liquidacion.py` (cohorte_id, periodo, usuario_id, rol, comisiones, monto_base, monto_plus, total, es_nexo, excluido_por_factura, estado)
- [x] 1.5 Crear `models/factura.py` (usuario_id, periodo, detalle, referencia_archivo, tamano_kb, estado, cargada_at, abonada_at)

## 2. Migración

- [x] 2.1 Crear migración Alembic con las 5 tablas + índices + FK

## 3. Repositorios

- [x] 3.1 Crear `repositories/salario_repository.py` (CRUD SalarioBase + SalarioPlus + MateriaGrupoPlus)
- [x] 3.2 Crear `repositories/liquidacion_repository.py` (CRUD Liquidacion + Factura)

## 4. Schemas

- [x] 4.1 Crear `schemas/salarios.py`
- [x] 4.2 Crear `schemas/liquidaciones.py`
- [x] 4.3 Crear `schemas/facturas.py`

## 5. Servicio

- [x] 5.1 Crear `services/liquidacion_service.py` con cálculo (RN-21, RN-34, PA-22, PA-23)

## 6. Routers

- [x] 6.1 Crear `routers/salarios.py` (bases, plus, grupos-materia CRUD)
- [x] 6.2 Crear `routers/liquidaciones.py` (generar, listar, detalle, cerrar, kpis)
- [x] 6.3 Crear `routers/facturas.py` (CRUD + abonar)
- [x] 6.4 Registrar routers en main.py

## 7. Tests

- [x] 7.1 Test: CRUD salario base
- [x] 7.2 Test: CRUD salario plus
- [x] 7.3 Test: CRUD materia_grupo_plus
- [x] 7.4 Test: Generar liquidación calcula base + plus
- [x] 7.5 Test: Plus acumula N × comisiones con tope (PA-23)
- [x] 7.6 Test: Cerrar liquidación la vuelve inmutable
- [x] 7.7 Test: Facturas CRUD + abonar

## 8. Frontend

- [x] 8.1 Feature `liquidaciones/` con páginas de grilla, lista, detalle
- [x] 8.2 Feature `facturas/` con lista y detalle
- [x] 8.3 App.tsx + Sidebar
- [x] 8.4 Tests
