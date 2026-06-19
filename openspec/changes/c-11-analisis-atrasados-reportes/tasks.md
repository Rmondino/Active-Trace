# Tasks: C-11 analisis-atrasados-reportes

## Task List

- [x] **1. Permiso seed**: Agregar `atrasados:ver` al seed de permisos en tests y migración
- [x] **2. AnalisisService**: Servicio principal con `alumnos_atrasados`, `ranking_aprobadas`, `reporte_rapido`, `notas_finales`, `exportar_sin_corregir`, `monitor`
- [x] **3. Router**: `routers/analisis.py` con 6 endpoints + guard `atrasados:ver`
- [x] **4. Tests service**: `test_analisis_service.py` con datasets seedeados
- [x] **5. Tests router**: `test_router_analisis.py` con permisos, scopes, multi-tenant
- [x] **6. Safety Net**: Ejecutar tests existentes (311), confirmar baseline + nuevos tests

## Progress Tracking

| Task | Status | Files |
|------|--------|-------|
| 1. Permiso | ⬜ | `tests/conftest.py` (seed) |
| 2. Service | ⬜ | `services/analisis_service.py` |
| 3. Router | ⬜ | `routers/analisis.py`, `main.py` |
| 4. Tests service | ⬜ | `tests/test_services/test_analisis_service.py` |
| 5. Tests router | ⬜ | `tests/test_routers/test_router_analisis.py` |
