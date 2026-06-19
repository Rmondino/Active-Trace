## Context

C-20 agrega perfil propio (backend tiene GET pero falta PUT) y mensajería interna entre usuarios (backend no existe). Governance BAJO.

## Goals / Non-Goals

**Goals:**
- PUT /api/usuarios/me para editar perfil
- Modelo Mensaje + migration + service + router inbox
- Frontend perfil con edición
- Frontend inbox con lista, detalle, respuesta, nuevo mensaje

**Non-Goals:**
- No se implementa búsqueda de usuarios (selector básico)
- No hay notificaciones en tiempo real (WebSocket)
- No hay adjuntos en mensajes

## Decisions

### D1: Modelo Mensaje simple (sin hilos complejos)
- **Decisión**: Tabla `mensaje` con `id, tenant_id, remitente_id, destinatario_id, mensaje_padre_id (self-ref), asunto, cuerpo, leido, created_at`
- `mensaje_padre_id` permite armar hilos (respuesta a respuesta)
- No se necesita tabla separada de hilos

### D2: PUT /api/usuarios/me — PATCH parcial
- **Decisión**: Usar PUT con campos opcionales para actualizar solo lo enviado
- CUIL no se puede modificar (se ignora si se envía)
- El service descifra, actualiza y recifra los campos PII

### D3: Frontend en features separadas
- `features/perfil/` para perfil
- `features/inbox/` para mensajería
- Son conceptualmente distintas

## Backend File Structure
```
backend/app/models/mensaje.py
backend/app/repositories/mensaje_repository.py
backend/app/services/mensaje_service.py
backend/app/routers/inbox.py
backend/app/schemas/mensaje.py
```
