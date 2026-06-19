## Modelos

### Tarea
```python
class Tarea(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "tarea"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    materia_id: Mapped[str | None] = mapped_column(ForeignKey("materia.id"), nullable=True)
    asignado_a: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False, index=True)
    asignado_por: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendiente")
    descripcion: Mapped[str] = mapped_column(String(5000), nullable=False)
    contexto_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    asignado = relationship("User", foreign_keys=[asignado_a], lazy="selectin")
    asignador = relationship("User", foreign_keys=[asignado_por], lazy="selectin")
    materia = relationship("Materia", lazy="selectin")
```

### ComentarioTarea
```python
class ComentarioTarea(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "comentario_tarea"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tarea_id: Mapped[str] = mapped_column(ForeignKey("tarea.id"), nullable=False, index=True)
    autor_id: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    texto: Mapped[str] = mapped_column(String(2000), nullable=False)
    
    tarea = relationship("Tarea", lazy="selectin")
    autor = relationship("User", lazy="selectin")
```

## State machine
```python
VALID_TRANSITIONS = {
    "Pendiente": {"En progreso", "Cancelada"},
    "En progreso": {"Resuelta", "Cancelada"},
}

def validar_transicion_tarea(actual: str, nuevo: str) -> None:
    if actual not in VALID_TRANSITIONS:
        raise ValueError(f"Estado terminal '{actual}': no permite transiciones")
    if nuevo not in VALID_TRANSITIONS[actual]:
        raise ValueError(f"Transición inválida: {actual} → {nuevo}")
```

## Service

```python
class TareaService:
    async def crear(self, data, user_id, tenant_id) -> Tarea
    async def mis_tareas(self, usuario_id, tenant_id, filtros) -> list
    async def listar_todas(self, tenant_id, filtros) -> list  # admin
    async def detalle(self, id, tenant_id) -> dict
    async def cambiar_estado(self, id, nuevo_estado, usuario_id, tenant_id) -> Tarea
    async def agregar_comentario(self, tarea_id, texto, autor_id, tenant_id) -> ComentarioTarea
```

## Router

```python
router = APIRouter(prefix="/api/tareas", tags=["tareas"])

@router.post("", status_code=201, dependencies=[Depends(require_permission("tareas:gestionar"))])
@router.get("", dependencies=[Depends(require_permission("tareas:gestionar"))])  # admin all
@router.get("/mias")  # any authenticated — their own tasks
@router.get("/{id}")  # any if involved
@router.patch("/{id}/estado")  # asignado or admin
@router.post("/{id}/comentarios", status_code=201)  # any if involved
```

## Tests

- Crear tarea con asignado_a, asignado_por
- Mis tareas: solo las del usuario
- Admin: todas con filtros
- Estado: Pendiente→En progreso→Resuelta (válido)
- Estado: Resuelta→Pendiente (inválido → error)
- Comentarios: agregar, listar en detalle
- 403 sin permiso
- Multi-tenant
