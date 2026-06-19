## Why

El usuario no puede editar su perfil ni comunicarse con otros usuarios del sistema. C-20 agrega la edición de perfil propio (nombre, datos fiscales/bancarios, regional) y una bandeja de mensajería interna entre usuarios registrados, paralela al sistema de comunicaciones a alumnos (C-12).

## What Changes

**Backend:**
- `PUT /api/usuarios/me` — editar perfil propio (CUIL no modificable, solo lectura)
- Modelo `Mensaje` con hilo/conversación, destinatario, cuerpo, leído
- Servicio de mensajería con creación de mensajes y listado de hilos
- `POST /api/inbox/enviar` — enviar mensaje a otro usuario
- `GET /api/inbox` — listar mensajes recibidos
- `GET /api/inbox/{id}` — ver detalle de mensaje (marca como leído)
- `POST /api/inbox/{id}/responder` — responder dentro del hilo
- Migración para tabla `mensaje`

**Frontend:**
- Página de perfil propio con formulario de edición
- Bandeja de entrada (inbox) con lista de mensajes recibidos
- Vista de detalle de mensaje con respuesta
- Componer nuevo mensaje a usuario

## Capabilities

### New Capabilities
- `perfil-edicion-ui`: Ver y editar perfil propio (nombre, datos bancarios, regional, CUIL solo lectura)
- `inbox-mensajeria`: Bandeja de entrada, detalle, responder, nuevo mensaje

### Modified Capabilities
- `user-profile` (backend): Agregar endpoint PUT /api/usuarios/me
- `app-layout`: Agregar items Perfil e Inbox al sidebar
- `frontend-shell`: Agregar rutas de perfil e inbox

## Impact

- **Backend nuevo**: Modelo Mensaje, migration, service, router inbox
- **Backend modificado**: Router usuarios_me.py (PUT), main.py (nuevo router)
- **Frontend nuevo**: features/perfil/, features/inbox/
- **Frontend modificado**: App.tsx, Sidebar.tsx
