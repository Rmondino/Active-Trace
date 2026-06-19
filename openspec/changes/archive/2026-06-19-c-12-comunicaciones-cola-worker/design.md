## Modelo de Datos

### Comunicacion

```python
class Comunicacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "comunicacion"

    id: Mapped[str]              # UUID PK
    enviado_por: Mapped[str]     # FK → User.id
    materia_id: Mapped[str]      # FK → Materia.id
    destinatario: Mapped[str]    # email cifrado AES-256-GCM [cifrado]
    asunto: Mapped[str]
    cuerpo: Mapped[str]
    estado: Mapped[str]          # Pendiente | Enviando | Enviado | Error | Cancelado
    lote_id: Mapped[str]         # UUID — batch grouping
    error_msg: Mapped[str | None]   # nullable
    aprobado_por: Mapped[str | None]  # FK → User.id, nullable
    aprobado_at: Mapped[datetime | None]
    enviado_at: Mapped[datetime | None]

    # relationships
    enviador = relationship("User", foreign_keys=[enviado_por], lazy="selectin")
    aprobador = relationship("User", foreign_keys=[aprobado_por], lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
```

**Indexes**:
- `(tenant_id, lote_id)` — para tracking por lote
- `(tenant_id, estado)` — para el worker que busca Pendientes
- `(tenant_id, materia_id)` — para tracking por materia

**Unicidad**: no aplica (muchos mensajes, cada uno es único por ID).

### Tenant config (JSONB)

Se usa el campo `config` existente del modelo `Tenant`:

```json
{
  "aprobacion_requerida": false,
  "aprobacion_umbral": 10
}
```

- `aprobacion_requerida`: bool, default false
- `aprobacion_umbral`: int, default 10 (cantidad de destinatarios que requieren aprobación)

## Repositorio

### ComunicacionRepository

```python
class ComunicacionRepository(BaseRepository[Comunicacion]):
    model_class = Comunicacion

    async def get_by_lote(self, lote_id: str) -> list[Comunicacion]
    async def get_by_materia(self, materia_id: str) -> list[Comunicacion]
    async def get_pendientes_aprobacion(self, tenant_id: str) -> list[Comunicacion]
    async def get_pendientes_envio(self, tenant_id: str, limit: int = 20) -> list[Comunicacion]
    async def bulk_create(self, comunicaciones: list[Comunicacion]) -> None
    async def actualizar_estado(self, id: str, estado: str, **kwargs) -> None
    async def count_by_lote(self, lote_id: str) -> dict[str, int]  # counts per estado
```

## Servicios

### ComunicacionService

```python
class ComunicacionService:
    def __init__(self, repo, email_sender, cipher_service, audit_log_service, tenant_repo):
        ...

    async def generar_preview(
        self, materia_id: str, asunto_template: str, cuerpo_template: str,
        alumnos: list[dict], tenant_id: str
    ) -> list[dict]:
        """
        Renderiza los templates para cada alumno.
        Sustituye variables: {alumno_nombre}, {alumno_apellidos}, {materia}, {comision}
        No persiste nada.
        """

    async def encolar(
        self, materia_id: str, lote_id: str | None,
        asunto: str, cuerpo: str,
        destinatarios: list[dict],  # [{entrada_padron_id, email, nombre, apellidos}]
        user_id: str, tenant_id: str
    ) -> dict:
        """
        Crea los registros Comunicacion en estado Pendiente.
        Si el tenant tiene aprobacion_requerida y el lote supera el umbral,
        los deja Pendiente (esperando aprobación).
        Si no, quedan Pendiente para que el worker los tome.
        Retorna: { lote_id, total, requiere_aprobacion }
        """

    async def aprobar_lote(self, lote_id: str, aprobador_id: str, tenant_id: str) -> dict:
        """
        Aprueba todos los mensajes Pendiente de un lote.
        Setea aprobado_por, aprobado_at.
        Los mensajes quedan Pendiente para que el worker los tome.
        """

    async def aprobar(self, comunicacion_id: str, aprobador_id: str, tenant_id: str) -> dict:
        """Aprueba un mensaje individual."""
        ...

    async def rechazar(self, comunicacion_id: str, tenant_id: str) -> dict:
        """Cancela un mensaje: estado → Cancelado."""
        ...

    async def tracking(self, materia_id: str, lote_id: str | None, tenant_id: str) -> list[dict]:
        """Estado de comunicaciones para una materia o lote."""
        ...
```

### EmailSender (interfaz)

```python
class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        """Returns True if sent, False if failed."""
        ...

class SmtpEmailSender(EmailSender):
    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str):
        ...

    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send via SMTP using aiosmtplib."""
        ...
```

### Worker (`workers/main.py`)

```python
class ComunicacionWorker:
    def __init__(self, session_factory, email_sender, cipher_service):
        ...

    async def run(self):
        """Main loop."""
        while True:
            try:
                async with self.session_factory() as session:
                    repo = ComunicacionRepository(session)
                    pendientes = await repo.get_pendientes_envio(tenant_id=None, limit=20)
                    # Wait — need to handle multi-tenant
                    # Actually: get ALL Pendientes that are ready (approved or no approval needed)
                    for msg in pendientes:
                        await self._procesar(msg, session)
            except Exception as e:
                logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)

    async def _procesar(self, msg: Comunicacion, session):
        """Process a single message."""
        # 1. Transition to Enviando
        msg.estado = "Enviando"
        await session.flush()

        # 2. Decrypt recipient
        email = self.cipher_service.decrypt(msg.destinatario)

        # 3. Send email
        success = await self.email_sender.send(to=email, subject=msg.asunto, body=msg.cuerpo)

        # 4. Transition
        if success:
            msg.estado = "Enviado"
            msg.enviado_at = datetime.now(UTC)
        else:
            msg.estado = "Error"
            msg.error_msg = "SMTP delivery failed"

        await session.commit()
```

**Query for pendientes**:
```sql
SELECT * FROM comunicacion
WHERE tenant_id = :tid
  AND estado = 'Pendiente'
  AND deleted_at IS NULL
  AND (aprobado_por IS NOT NULL 
       OR NOT EXISTS (
           SELECT 1 FROM tenant t 
           WHERE t.id = comunicacion.tenant_id 
           AND (t.config->>'aprobacion_requerida')::boolean = true
       ))
ORDER BY created_at ASC
LIMIT 20
```

This query gets messages that are:
- Pendiente
- AND (approved OR tenant doesn't require approval)

## Preview Flow (RN-16)

```
1. POST /api/comunicaciones/preview
   Body: { materia_id, asunto_template: "Aviso importante para {alumno_nombre}", 
           cuerpo_template: "Hola {alumno_nombre}...", alumnos_ids: [...], template_vars: {...} }
   → Response: {
       previews: [
         { alumno_id, alumno_nombre: "Juan Pérez", asunto: "Aviso importante para Juan Pérez",
           cuerpo: "Hola Juan Pérez..." }
       ],
       preview_token: "uuid"  // REQUIRED for the next step
     }

2. User reviews the previews in the UI

3. POST /api/comunicaciones/enviar
   Body: { materia_id, preview_token, asunto_template, cuerpo_template, 
           destinatarios: [{entrada_padron_id, email, nombre, apellidos}], lote_id: null }
   → Response: { lote_id, total, requiere_aprobacion }
```

The `preview_token` ensures that preview was called before enqueue. Stored in memory with TTL (similar to C-09 preview).

## Approval Flow (RN-17)

```
1. POST /api/comunicaciones/enviar → mensajes Pendiente (si aprobacion_requerida=true)
2. GET /api/comunicaciones/pendientes-aprobacion → lista de mensajes Pendiente sin aprobar
3. POST /api/comunicaciones/aprobar/lote/{lote_id} → aprueba todo el lote
   O POST /api/comunicaciones/aprobar/{id} → aprueba individual
   O POST /api/comunicaciones/rechazar/{id} → rechaza → Cancelado
4. Worker agarra los aprobados y los envía
```

## Endpoints

| Método | Ruta | Permiso | Body/Params | Response |
|--------|------|---------|-------------|----------|
| `POST` | `/api/comunicaciones/preview` | `comunicacion:enviar` | `{ materia_id, asunto_template, cuerpo_template, alumnos_ids }` | `{ previews: [...], preview_token }` |
| `POST` | `/api/comunicaciones/enviar` | `comunicacion:enviar` | `{ materia_id, preview_token, asunto, cuerpo, destinatarios }` | `{ lote_id, total, requiere_aprobacion }` |
| `GET` | `/api/comunicaciones?materia_id=X` | `comunicacion:enviar` | query | `[{ id, destinatario_mask, estado, ... }]` |
| `GET` | `/api/comunicaciones/pendientes-aprobacion` | `comunicacion:aprobar` | — | `[{ lote_id, materia, count }]` |
| `POST` | `/api/comunicaciones/aprobar/lote/{lote_id}` | `comunicacion:aprobar` | — | `{ aprobados: N }` |
| `POST` | `/api/comunicaciones/aprobar/{id}` | `comunicacion:aprobar` | — | `{ estado: "Pendiente" }` |
| `POST` | `/api/comunicaciones/rechazar/{id}` | `comunicacion:aprobar` | — | `{ estado: "Cancelado" }` |

## Config (Settings)

Agregar a `Settings`:
```python
EMAIL_SMTP_HOST: str = Field(default="localhost")
EMAIL_SMTP_PORT: int = Field(default=587)
EMAIL_SMTP_USERNAME: str | None = Field(default=None)
EMAIL_SMTP_PASSWORD: str | None = Field(default=None)
EMAIL_FROM_ADDR: str = Field(default="noreply@activia-trace.com")
```

## Worker Startup

El worker se lanza separadamente de la API:
```bash
python -m app.workers.main
```

En docker-compose, es un servicio aparte que corre el mismo container pero con entrypoint distinto.

## Migración 008

```sql
CREATE TABLE comunicacion (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL REFERENCES tenant(id),
    enviado_por VARCHAR NOT NULL REFERENCES usuario(id),
    materia_id VARCHAR NOT NULL REFERENCES materia(id),
    destinatario TEXT NOT NULL,       -- cifrado
    asunto TEXT NOT NULL,
    cuerpo TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    lote_id VARCHAR NOT NULL,
    error_msg TEXT,
    aprobado_por VARCHAR REFERENCES usuario(id),
    aprobado_at TIMESTAMPTZ,
    enviado_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_comunicacion_lote ON comunicacion (tenant_id, lote_id);
CREATE INDEX idx_comunicacion_estado ON comunicacion (tenant_id, estado);
CREATE INDEX idx_comunicacion_materia ON comunicacion (tenant_id, materia_id);
```

## Tests (TDD estricto — governance ALTO)

### Safety Net
- Ejecutar tests existentes (344 tests), capturar baseline.

### Modelo
- Crear Comunicacion, todos los campos, estados válidos.
- Soft delete, multi-tenant, timestamps.

### Repositorio
- CRUD, bulk_create, get_pendientes_envio, get_pendientes_aprobacion.
- actualizar_estado transiciona correctamente.
- Aislamiento multi-tenant.

### ComunicacionService
- Preview: renderiza templates {alumno_nombre} correctamente.
- Encolar: crea registros Pendiente, bulk.
- Encolar con aprobacion_requerida → Pendiente.
- Encolar sin aprobacion_requerida → Pendiente listo para worker.
- Aprobar lote: setea aprobado_por + aprobado_at.
- Rechazar: estado → Cancelado.

### EmailSender
- SMTP send → OK retorna True.
- SMTP connection fail → retorna False.
- (Mockeado en tests unitarios)

### Router
- 403 sin permiso.
- Preview requiere alumno_ids válidos.
- Enviar requiere preview_token.
- Aprobar: 403 sin comunicacion:aprobar.
- Tracking returns estados correctos.

### Worker
- Procesa mensaje Pendiente → Enviando → Enviado.
- Error de envío → Enviando → Error con error_msg.
- Salta mensajes que requieren aprobación (aprobado_por IS NULL).
- No se traba por errores de un mensaje (sigue con el siguiente).
