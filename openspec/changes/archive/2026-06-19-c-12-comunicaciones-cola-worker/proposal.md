## Why

Tenemos todo el pipeline de datos: importar calificaciones → detectar atrasados → analizar. Pero el sistema todavía **no puede comunicarse** con los alumnos. Toda la detección de atrasados queda en un reporte que el docente mira — no genera acción concreta.

C-12 cierra el círculo: permite **enviar comunicaciones** a los alumnos desde el sistema, con preview obligatorio (RN-16), cola de despacho asincrónica (RN-15), y aprobación configurable por tenant (RN-17).

Es el **último change del camino crítico**: después de esto, el flujo completo importar → analizar → comunicar funciona end-to-end.

## What Changes

### Modelo Comunicacion

```python
Comunicacion {
    id              : UUID       — PK
    tenant_id       : UUID       — FK → Tenant
    enviado_por     : UUID       — FK → Usuario (quién disparó el envío)
    materia_id      : UUID       — FK → Materia
    destinatario    : texto      — email cifrado AES-256-GCM [cifrado]
    asunto          : texto
    cuerpo          : texto      — cuerpo del mensaje (texto enriquecido plano)
    estado          : enum       — Pendiente | Enviando | Enviado | Error | Cancelado
    lote_id         : UUID       — agrupa envíos masivos de una misma acción
    error_msg       : texto      — nullable; detalle del error si estado=Error
    aprobado_por    : UUID       — nullable; FK → Usuario (quién aprobó)
    aprobado_at     : fecha-hora — nullable
    enviado_at      : fecha-hora — nullable
}
```

Transiciones de estado (RN-15):
```
Pendiente ──→ Enviando ──→ Enviado
    │                       │
    │                       │
    ├──→ Cancelado          └──→ Error (con error_msg)
    │
    └──→ (si aprobación requerida: espera aprobación)
          Pendiente ─→ (aprobado) ─→ Enviando
                     ─→ (rechazado) ─→ Cancelado
```

### Tenant config: `aprobacion_requerida`

Se agrega dentro del JSONB `config` del Tenant:
```json
{
  "aprobacion_requerida": true/false,
  "aprobacion_umbral": 10  // cantidad de destinatarios que gatilla aprobación
}
```

- `false`: los mensajes pasan directo Pendiente → Worker
- `true`: Pendiente requiere aprobación explícita de `comunicacion:aprobar`

Si el tenant tiene `aprobacion_requerida=True` y el lote supera `aprobacion_umbral` destinatarios, los mensajes quedan en Pendiente hasta que un aprobador los libere.

### Preview obligatorio (RN-16)

```
POST /api/comunicaciones/preview
Body: { materia_id, asunto_template, cuerpo_template, alumnos_ids: [entrada_padron_ids] }
→ Response: { previews: [{ alumno_nombre, asunto, cuerpo }] }
```

- NO se puede llamar al envío sin haber llamado a preview primero
- El preview renderiza templates: `{alumno_nombre}`, `{alumno_apellidos}`, `{materia}`, `{comision}`
- El frontend muestra el preview, el usuario confirma → recién ahí se llama al envío

### Worker asíncrono

Se reemplaza el placeholder actual en `workers/main.py` por un worker real:

```
Worker loop (asyncio, poll cada 5s):
  1. Query Comunicacion WHERE estado = 'Pendiente'
     AND (aprobado_por IS NOT NULL OR NOT aprobacion_requerida)
  2. Batch: tomar hasta 20 mensajes
  3. Por cada uno:
     a. Transicionar a Enviando (UPDATE estado)
     b. Descifrar destinatario (CipherService)
     c. Enviar email vía SMTP/API
     d. OK → estado=Enviado, enviado_at=now()
        Error → estado=Error, error_msg=str(e)
  4. Esperar 5s y repetir
```

**Envío de emails**: interfaz `EmailSender` con implementación SMTP base:
```python
class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool: ...
```

Implementación concreta: `SmtpEmailSender` (config: host, port, user, pass, from).

### Endpoints

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `POST` | `/api/comunicaciones/preview` | `comunicacion:enviar` | Generar preview de mensajes (RN-16) |
| `POST` | `/api/comunicaciones/enviar` | `comunicacion:enviar` | Encolar mensajes (requiere preview previo) |
| `GET` | `/api/comunicaciones?materia_id=X&lote_id=Y` | `comunicacion:enviar` | Tracking de estado por materia/lote |
| `GET` | `/api/comunicaciones/pendientes-aprobacion` | `comunicacion:aprobar` | Cola de mensajes pendientes de aprobar |
| `POST` | `/api/comunicaciones/aprobar/lote/{lote_id}` | `comunicacion:aprobar` | Aprobar lote completo |
| `POST` | `/api/comunicaciones/aprobar/{id}` | `comunicacion:aprobar` | Aprobar mensaje individual |
| `POST` | `/api/comunicaciones/rechazar/{id}` | `comunicacion:aprobar` | Rechazar → Cancelado |

### Permisos
- `comunicacion:enviar` — preview + enqueue
- `comunicacion:aprobar` — aprobar/rechazar

### Migración
- `008_create_comunicacion` — tabla comunicacion
- Agregar campo config `aprobacion_requerida` no requiere migración (ya es JSONB)

### Impact

- **Modelo**: `backend/app/models/comunicacion.py` (nuevo).
- **Migración 008**: tabla `comunicacion`.
- **Servicios**: `ComunicacionService` (preview, enqueue, aprobar, tracking), `EmailSender` (SMTP).
- **Worker**: `workers/main.py` reemplazado con loop real.
- **Router**: `routers/comunicaciones.py`.
- **Auditoría**: `COMUNICACION_ENVIAR` al encolar.
- **Config**: agregar `EMAIL_*` vars a Settings.
- **Dependencias**: `aiosmtplib` o similar para SMTP async.
