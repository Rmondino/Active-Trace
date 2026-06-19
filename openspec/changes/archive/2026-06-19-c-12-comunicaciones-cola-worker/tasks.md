# Tasks: C-12 comunicaciones-cola-worker

## Task List

- [x] **1. Modelo**: Crear `Comunicacion` en `backend/app/models/comunicacion.py`
- [x] **2. Migración 008**: Generar migración Alembic con `comunicacion` + índices
- [x] **3. State machine**: Servicio/helper con validación de transiciones (RN-15)
- [x] **4. Repositorio**: `ComunicacionRepository` con bulk_create, get_pendientes_envio, get_pendientes_aprobacion, actualizar_estado
- [x] **5. Preview service**: `ComunicacionService.generar_preview` con templates + preview_token (30min exp, single-use)
- [x] **6. Enqueue service**: `ComunicacionService.encolar` con verificación de approval tenant config
- [x] **7. Approval service**: `ComunicacionService.aprobar_lote`, `aprobar`, `rechazar`
- [x] **8. EmailSender**: Interfaz + `SmtpEmailSender` (aiosmtplib)
- [x] **9. Worker**: Reemplazar `workers/main.py` con loop asyncio real que procesa Pendientes
- [x] **10. Router**: `routers/comunicaciones.py` con 7 endpoints + guards
- [x] **11. Config**: Agregar `EMAIL_*` vars a Settings
- [x] **12. Audit**: Integrar `COMUNICACION_ENVIAR` al encolar
- [x] **13. Tests modelo**: Test Comunicacion model + state machine transitions
- [x] **14. Tests repositorio**: Test CRUD, pendientes, approvals
- [x] **15. Tests service**: Test preview, enqueue, approval, state validation
- [x] **16. Tests router**: Test endpoints, permisos, preview token, transitions
- [x] **17. Safety Net**: Ejecutar tests existentes (344), confirmar baseline + nuevos tests

## Progress Tracking

| Task | Status | Files |
|------|--------|-------|
| 1. Modelo | ✅ | `models/comunicacion.py`, `models/__init__.py` |
| 2. Migración | ✅ | `alembic/versions/008_create_comunicacion.py` |
| 3. State machine | ✅ | `services/comunicacion_service.py` (validador) |
| 4. Repositorio | ✅ | `repositories/comunicacion_repository.py` |
| 5-7. Service | ✅ | `services/comunicacion_service.py` |
| 8. EmailSender | ✅ | `integrations/email_sender.py` |
| 9. Worker | ✅ | `workers/main.py` |
| 10. Router | ✅ | `routers/comunicaciones.py`, `main.py` |
| 11. Config | ✅ | `core/config.py` |
| 12. Audit | ✅ | Integrado en encolar/aprobar/rechazar |
| 13. Tests modelo | ✅ | `tests/test_models/test_comunicacion_model.py` |
| 14. Tests repositorio | ✅ | `tests/test_models/test_comunicacion_repo.py` |
| 15. Tests service | ✅ | `tests/test_services/test_comunicacion_service.py` |
| 16. Tests router | ✅ | `tests/test_routers/test_router_comunicaciones.py` |
| 17. Safety Net | ✅ | 403 passed (344 original + 59 nuevos) |
