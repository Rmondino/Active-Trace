## Model: AuditLog (expandido)

```python
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id: Mapped[str]          # UUID PK
    actor_id: Mapped[str]    # FK → User (quien ejecutó la acción)
    impersonado_id: Mapped[str | None]  # FK → User (nullable, quién fue impersonado)
    tenant_id: Mapped[str]   # FK → Tenant
    materia_id: Mapped[str | None]  # FK → Materia (nullable)
    accion: Mapped[str]      # código estandarizado
    detalle: Mapped[dict | None]  # JSONB
    filas_afectadas: Mapped[int | None]  # nullable
    ip: Mapped[str | None]
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime]  # fecha_hora
```

**Append-only**: AuditLogRepository NO hereda de BaseRepository — solo expone `create()`, `get()`, `get_all()`, `get_by_filtros()`. Sin update, sin delete.

## Service: AuditLogService

Expandir con:
```python
async def log(self, actor_id, tenant_id, accion, materia_id=None, detalle=None, 
              filas_afectadas=None, ip=None, user_agent=None, impersonado_id=None) -> AuditLog

async def get_all(self, tenant_id, filtros: dict, limit: int = 200) -> list[AuditLog]
    # Filtros: accion, materia_id, actor_id, desde (date), hasta (date), limit
```

## Impersonación

### Permiso nuevo
- `impersonacion:usar` para COORDINADOR, ADMIN

### Endpoints
```
POST /api/auth/impersonar
Body: { "usuario_id": "uuid" }
→ Response: { "access_token": "...", "token_type": "bearer", "impersonando": true }

POST /api/auth/dejar-impersonar
→ Response: { "access_token": "...", "token_type": "bearer", "impersonando": false }
```

### JWT claims expandidos
```json
{
  "sub": "user-id-impersonado",
  "tenant_id": "...",
  "actor_original_id": "user-id-real",
  "impersonando": true,
  "exp": ...
}
```

### Flujo impersonación
1. Usuario con `impersonacion:usar` llama a `POST /api/auth/impersonar { usuario_id }`
2. Sistema verifica: permiso, usuario_id destino existe en mismo tenant
3. Genera JWT con `sub=usuario_destino`, `actor_original_id=usuario_real`, `impersonando=true`
4. Registra audit `IMPERSONACION_INICIAR` con actor_real→usuario_impersonado
5. Cuando termina: `POST /api/auth/dejar-impersonar` → JWT original + audit `IMPERSONACION_FINALIZAR`

### En AuditLogService
- Si `impersonado_id` está presente, se registra en el log
- El actor real es siempre `actor_id`, el impersonado es `impersonado_id`

## Router: auditoria

```python
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/auditoria", dependencies=[Depends(require_permission("auditoria:ver"))])
async def listar_auditoria(
    accion: str | None = None,
    materia_id: str | None = None,
    actor_id: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = 200,
    ...
)
```

## Tests (CRITICAL governance)

- **Append-only**: AuditLogRepository sin update/delete
- **Log creation**: with all fields incl. filas_afectadas, user_agent
- **Impersonación iniciar**: 200 con JWT distinguible
- **Impersonación sin permiso**: 403
- **Impersonación dejar**: restaura JWT original
- **Audit entries**: IMPERSONACION_INICIAR y FINALIZAR registrados
- **Query**: filtros funcionan, multi-tenant isolation
