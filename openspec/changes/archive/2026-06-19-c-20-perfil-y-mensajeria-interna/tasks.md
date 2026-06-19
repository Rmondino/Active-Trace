## 1. Backend — Perfil PUT

- [x] 1.1 Agregar endpoint `PUT /api/usuarios/me` en `backend/app/routers/usuarios_me.py`
- [x] 1.2 Crear schema `PerfilUpdate` con campos editables (CUIL excluido)
- [x] 1.3 Agregar método `update_profile` en user repository o inline en router

## 2. Backend — Modelo Mensaje

- [x] 2.1 Crear `backend/app/models/mensaje.py` con SQLAlchemy model
- [x] 2.2 Crear migración Alembic para tabla `mensaje`

## 3. Backend — Repositorio + Servicio Mensaje

- [x] 3.1 Crear `backend/app/repositories/mensaje_repository.py`
- [x] 3.2 Crear `backend/app/services/mensaje_service.py` (enviar, listar recibidos, detalle, responder, marcar leído)

## 4. Backend — Router Inbox

- [x] 4.1 Crear `backend/app/routers/inbox.py` con schemas + endpoints
- [x] 4.2 Registrar router en `backend/app/main.py`

## 5. Backend — Tests

- [x] 5.1 Test: PUT /api/usuarios/me actualiza perfil
- [x] 5.2 Test: Mensaje CRUD (enviar, listar, detalle, responder)

## 6. Frontend — Perfil

- [x] 6.1 Crear `features/perfil/services/perfilService.ts` (GET + PUT)
- [x] 6.2 Crear `features/perfil/hooks/usePerfil.ts`
- [x] 6.3 Crear `features/perfil/pages/PerfilPage.tsx` con formulario de edición
- [x] 6.4 Agregar ruta `/perfil` en App.tsx
- [x] 6.5 Agregar item "Mi Perfil" en Sidebar.tsx

## 7. Frontend — Inbox

- [x] 7.1 Crear `features/inbox/services/inboxService.ts`
- [x] 7.2 Crear `features/inbox/hooks/useInbox.ts`
- [x] 7.3 Crear `features/inbox/pages/InboxPage.tsx` (lista de mensajes)
- [x] 7.4 Crear `features/inbox/pages/InboxDetailPage.tsx` (detalle + responder)
- [x] 7.5 Crear `features/inbox/pages/NuevoMensajePage.tsx`
- [x] 7.6 Agregar rutas `/inbox`, `/inbox/{id}`, `/inbox/nuevo` en App.tsx
- [x] 7.7 Agregar item "Mensajes" en Sidebar.tsx

## 8. Tests Frontend

- [x] 8.1 Test: PerfilPage render y formulario
- [x] 8.2 Test: InboxPage render con mensajes
