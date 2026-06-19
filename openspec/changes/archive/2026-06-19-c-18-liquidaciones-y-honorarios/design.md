## Context

Módulo financiero completo. PA-22 y PA-23 resueltas (ver knowledge-base). Governance CRÍTICO.

## Decisions

### D1: Cálculo en servicio dedicado
- Un `LiquidacionService.calcular(cohorte_id, periodo)` recorre todas las asignaciones activas, calcula base + plus por grupo, y crea Liquidacion records

### D2: Algoritmo de plus (PA-23)
- Por cada grupo donde el docente tenga comisiones: N = cantidad de comisiones activas, N_efectivo = min(N, SalarioPlus.tope_acumulacion), monto += SalarioPlus.monto × N_efectivo

### D3: Facturas con file upload
- El archivo PDF se guarda en disco local (referencia_archivo como path). En producción iría a S3/GCS.

## File Structure
```
backend/app/
├── models/
│   ├── salario_base.py
│   ├── salario_plus.py
│   ├── materia_grupo_plus.py
│   ├── liquidacion.py
│   └── factura.py
├── repositories/
│   ├── salario_repository.py
│   └── liquidacion_repository.py
├── services/
│   └── liquidacion_service.py
├── routers/
│   ├── salarios.py
│   ├── liquidaciones.py
│   └── facturas.py
└── schemas/
    ├── salarios.py
    ├── liquidaciones.py
    └── facturas.py
```
