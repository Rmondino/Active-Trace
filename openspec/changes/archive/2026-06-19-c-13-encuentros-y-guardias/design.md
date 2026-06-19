## Modelos

### SlotEncuentro

```python
class SlotEncuentro(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "slot_encuentro"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asignacion_id: Mapped[str] = mapped_column(ForeignKey("asignacion.id"), nullable=False)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    dia_semana: Mapped[str | None] = mapped_column(String(10), nullable=True)  # recurrente: "Lunes"...
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)  # recurrente
    cant_semanas: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0 = fecha única
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)  # único alternativa
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date] = mapped_column(Date, nullable=False)
```

**RN-13**: Recurrente si `cant_semanas > 0` (usa dia_semana, fecha_inicio, cant_semanas). Único si `cant_semanas = 0` (usa fecha_unica). Excluyentes.

### InstanciaEncuentro

```python
class InstanciaEncuentro(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "instancia_encuentro"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slot_id: Mapped[str | None] = mapped_column(ForeignKey("slot_encuentro.id"), nullable=True)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Programado")  # Programado|Realizado|Cancelado
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(String(1000), nullable=True)
```

**RN-14**: Cada instancia tiene estado independiente del slot. Editar instancia no afecta slot ni otras instancias.

### Guardia

```python
class Guardia(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "guardia"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asignacion_id: Mapped[str] = mapped_column(ForeignKey("asignacion.id"), nullable=False)
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False, index=True)
    carrera_id: Mapped[str | None] = mapped_column(ForeignKey("carrera.id"), nullable=True)
    cohorte_id: Mapped[str | None] = mapped_column(ForeignKey("cohorte.id"), nullable=True)
    dia: Mapped[str] = mapped_column(String(10), nullable=False)  # día de semana
    horario: Mapped[str] = mapped_column(String(20), nullable=False)  # "14:00–14:45"
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendiente")  # Pendiente|Realizada|Cancelada
    comentarios: Mapped[str | None] = mapped_column(String(1000), nullable=True)
```

## Servicios

### EncuentroService

```python
class EncuentroService:
    async def crear_slot(self, data, user_id, tenant_id) -> SlotEncuentro | list[InstanciaEncuentro]:
        """Crea slot y genera instancias según RN-13.
        Si cant_semanas > 0: recurrente → genera N instancias semanales desde fecha_inicio.
        Si cant_semanas == 0: único → genera 1 instancia en fecha_unica."""
        # Crear slot
        # Generar instancias
        # Retornar slot + instancias

    async def editar_instancia(self, id, data, tenant_id) -> InstanciaEncuentro:
        """Edita estado, meet_url, video_url, comentario (RN-14: no afecta slot)."""
        
    async def listar_slots(self, materia_id, tenant_id) -> list[SlotEncuentro]:
        """Slots de una materia."""
        
    async def listar_instancias(self, materia_id, tenant_id) -> list[InstanciaEncuentro]:
        """Instancias de una materia."""
        
    async def generar_contenido_aula(self, materia_id, tenant_id) -> str:
        """Genera bloque HTML con tabla de encuentros."""
        
    async def vista_admin(self, tenant_id, filtros) -> list:
        """Vista transversal de todos los encuentros del tenant."""
```

**Generación de instancias recurrentes**:
```python
instancias = []
for i in range(cant_semanas):
    fecha = fecha_inicio + timedelta(weeks=i)
    # Verificar que fecha cae en el día correcto de semana
    instancia = InstanciaEncuentro(
        slot_id=slot.id, materia_id=..., fecha=fecha, hora=slot.hora,
        titulo=slot.titulo, estado="Programado", meet_url=slot.meet_url,
        tenant_id=tenant_id,
    )
    instancias.append(instancia)
```

### GuardiaService

```python
class GuardiaService:
    async def registrar(self, data, user_id, tenant_id) -> Guardia:
        """Registra una guardia (TUTOR registra propia, COORDINADOR puede registrar cualquier)."""
        
    async def listar(self, materia_id, tenant_id, filtros) -> list[Guardia]:
        """Listar con filtros."""
        
    async def exportar(self, materia_id, tenant_id) -> bytes:
        """Genera xlsx con guardias."""
```

## Router

### `/api/encuentros/*`

```python
router_encuentros = APIRouter(prefix="/api/encuentros", tags=["encuentros"])

@router_encuentros.post("/slots", status_code=201, dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.get("/slots", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.get("/slots/{id}", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.patch("/instancias/{id}", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.get("/instancias", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.get("/contenido-aula", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_encuentros.get("/vista-admin", dependencies=[Depends(require_permission("encuentros:gestionar"))])
```

### `/api/guardias/*`

```python
router_guardias = APIRouter(prefix="/api/guardias", tags=["guardias"])

@router_guardias.post("", status_code=201, dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_guardias.get("", dependencies=[Depends(require_permission("encuentros:gestionar"))])
@router_guardias.get("/export", dependencies=[Depends(require_permission("encuentros:gestionar"))])
```

## Tests

- Slot recurrente: genera N instancias en las fechas correctas
- Slot único: genera 1 instancia
- Editar instancia: no afecta slot ni otras instancias
- Contenido aula: genera HTML con tabla
- Vista admin: retorna todos los encuentros
- Guardia: CRUD, registro, listado, export
- Multi-tenant isolation
- 403 sin permiso
