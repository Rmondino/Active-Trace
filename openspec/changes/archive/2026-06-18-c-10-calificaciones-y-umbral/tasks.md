# Tasks: C-10 calificaciones-y-umbral

## Task List

- [x] **1. Modelos**: Crear `Calificacion` y `UmbralMateria` en `backend/app/models/`
- [x] **2. Migración 007**: Generar migración Alembic con `calificacion` y `umbral_materia`
- [x] **3. Repositorios**: `CalificacionRepository` y `UmbralMateriaRepository`
- [x] **4. Calificaciones Parser**: Servicio de parseo con detección (Real) → numérica, preview, derivación aprobado
- [x] **5. Router import**: `POST /api/calificaciones/import` con preview y `?confirm=true`
- [x] **6. Router confirm**: `POST /api/calificaciones/preview/{preview_id}/confirm`
- [x] **7. Router completions**: `POST /api/calificaciones/import/completions` (F1.2, RN-07/08)
- [x] **8. Router calificaciones**: `GET /api/calificaciones?materia_id=X`
- [x] **9. Router umbral**: `GET/PUT /api/umbral` + `GET /api/umbral/default`
- [x] **10. Audit**: Integrar registro `CALIFICACIONES_IMPORTAR` en import y confirm
- [x] **11. Tests modelos**: Test TDD para Calificacion y UmbralMateria
- [x] **12. Tests repositorios**: Test CRUD, bulk_create, upsert, get_default
- [x] **13. Tests parser**: Test parseo con (Real), numérica vs textual, preview, derivación aprobado
- [x] **14. Tests routers**: Test import, confirm, completions, umbral, permisos 403, multi-tenant
- [x] **15. Tests audit**: Test que import y confirm generan audit `CALIFICACIONES_IMPORTAR`
- [x] **16. Safety Net**: Ejecutar tests existentes (231), confirmar baseline + nuevos tests

## Progress Tracking

| Task | Status | Files |
|------|--------|-------|
| 1. Modelos | ✅ | `calificacion.py`, `umbral_materia.py`, `__init__.py` |
| 2. Migración | ✅ | `alembic/versions/007_create_calificacion_umbral_materia.py` |
| 3. Repositorios | ✅ | `calificacion_repository.py`, `umbral_materia_repository.py`, `__init__.py` |
| 4. Parser | ✅ | `services/calificaciones_parser.py` |
| 5-8. Routers | ✅ | `routers/calificaciones.py`, `routers/umbral.py`, `main.py` |
| 9. Audit | ✅ | integrado en routers (`CALIFICACIONES_IMPORTAR`) |
| 10-15. Tests | ✅ | 5 test files en `tests/` |
