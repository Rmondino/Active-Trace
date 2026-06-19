# Tasks: C-09 padron-ingesta-moodle

## Task List

- [x] **1. Setup**: Agregar `openpyxl` a `pyproject.toml` en `dependencies`
- [x] **2. Modelos**: Crear `VersionPadron` y `EntradaPadron` en `backend/app/models/`
- [x] **3. Migración 006**: Generar migración Alembic con `version_padron`, `entrada_padron` y `audit_log`
- [x] **4. Repositorios**: `VersionPadronRepository` y `EntradaPadronRepository`
- [x] **5. File Parser**: Servicio de parseo para `.xlsx` (openpyxl) y `.csv` (csv module) con preview
- [x] **6. Moodle WS Client**: `integrations/moodle_ws.py` con retry, errores, y métodos sync
- [x] **7. Router import**: `POST /api/padron/import` con preview y `?confirm=true`
- [x] **8. Router preview/confirm**: `POST /api/padron/preview/{preview_id}/confirm`
- [x] **9. Router vaciar**: `DELETE /api/padron/materia/{materia_id}` con audit `PADRON_CARGAR`
- [x] **10. Router versiones**: `GET /api/padron/versiones` list/detail
- [x] **11. Router moodle sync**: `GET /api/padron/moodle/sync` on-demand
- [x] **12. Auditoría**: Integrar registro `PADRON_CARGAR` en import, confirm y vaciar
- [x] **13. Tests model/version_padron**: Test TDD para VersionPadron (5 tests)
- [x] **14. Tests model/entrada_padron**: Test TDD para EntradaPadron (incluido en 13)
- [x] **15. Tests repositorios**: Test CRUD, bulk_create, versión activa, vaciar (13 tests)
- [x] **16. Tests parser**: Test parseo xlsx, csv, errores, preview (9 tests)
- [x] **17. Tests moodle client**: Test sync, retry, errores con mock (6 tests)
- [x] **18. Tests routers**: Test import, confirm, vaciar, list, moodle sync, permisos (9 tests)
- [x] **19. Tests auditoría**: Test que import y vaciar generan audit `PADRON_CARGAR`
- [x] **20. Safety Net + TDD Cycle**: Ejecutar tests existentes, confirmar baseline + nuevos tests

## Progress Tracking

| Task | Status | Files |
|------|--------|-------|
| 1. Setup | ✅ | `backend/pyproject.toml` |
| 2. Modelos | ✅ | `backend/app/models/version_padron.py`, `entrada_padron.py`, `audit_log.py`, `__init__.py` |
| 3. Migración | ✅ | `alembic/versions/006_create_version_padron_entrada_padron.py` |
| 4. Repositorios | ✅ | `backend/app/repositories/version_padron_repository.py`, `entrada_padron_repository.py` |
| 5. Parser | ✅ | `backend/app/services/padron_parser.py` |
| 6. Moodle WS | ✅ | `backend/app/integrations/moodle_ws.py` |
| 7-11. Routers | ✅ | `backend/app/routers/padron.py` |
| 12. Auditoría | ✅ | `backend/app/services/audit_log_service.py` |
| 13-20. Tests | ✅ | `backend/tests/test_version_padron_model.py`, `test_version_padron_repo.py`, `test_padron_parser.py`, `test_moodle_ws.py`, `test_router_padron.py` |
