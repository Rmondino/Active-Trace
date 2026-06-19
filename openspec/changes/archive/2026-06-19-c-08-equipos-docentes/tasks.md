# Tasks: C-08 equipos-docentes

## Task List

- [x] **1. EquipoService**: Servicio con mis_equipos, listar_asignaciones, asignacion_masiva, clonar_equipo, actualizar_vigencia, exportar_equipo
- [x] **2. Permiso**: `equipos:asignar` ya existía en seed de permisos (migración 003)
- [x] **3. Router**: `routers/equipos.py` con 6 endpoints, registrado en main.py
- [x] **4. Audit**: `ASIGNACION_MODIFICAR` en masiva, clonar, vigencia
- [x] **5. Tests service**: `test_equipo_service.py` — 14 tests
- [x] **6. Tests router**: `test_router_equipos.py` — 11 tests
- [x] **7. Safety Net**: 428 passed (403 existing + 25 nuevos)

## Progress Tracking

| Task | Status | Files |
|------|--------|-------|
| 1. Service | ✅ | `services/equipo_service.py` |
| 2. Permiso | ✅ | ya existía en migración 003 |
| 3. Router | ✅ | `routers/equipos.py`, `main.py` |
| 4. Audit | ✅ | integrado en service |
| 5. Tests service | ✅ | `tests/test_services/test_equipo_service.py` |
| 6. Tests router | ✅ | `tests/test_routers/test_router_equipos.py` |
