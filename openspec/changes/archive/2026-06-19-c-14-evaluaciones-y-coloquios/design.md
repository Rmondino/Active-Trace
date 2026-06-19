## Modelos

### Evaluacion

```python
class Evaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "evaluacion"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False)
    cohorte_id: Mapped[str] = mapped_column(ForeignKey("cohorte.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="Coloquio")
    instancia: Mapped[str] = mapped_column(String(200), nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    cupo_por_dia: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
```

### ReservaEvaluacion

```python
class ReservaEvaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "reserva_evaluacion"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluacion_id: Mapped[str] = mapped_column(ForeignKey("evaluacion.id"), nullable=False, index=True)
    alumno_id: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")
    
    evaluacion = relationship("Evaluacion", lazy="selectin")
    alumno = relationship("User", lazy="selectin")
```

**Unicidad**: `(tenant_id, evaluacion_id, alumno_id)` — un alumno solo una reserva por convocatoria.

### ResultadoEvaluacion

```python
class ResultadoEvaluacion(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "resultado_evaluacion"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluacion_id: Mapped[str] = mapped_column(ForeignKey("evaluacion.id"), nullable=False, index=True)
    alumno_id: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False, index=True)
    nota_final: Mapped[str] = mapped_column(String(50), nullable=False)
    
    evaluacion = relationship("Evaluacion", lazy="selectin")
    alumno = relationship("User", lazy="selectin")
```

## Servicios

### ColoquioService

```python
class ColoquioService:
    async def crear(self, data, user_id, tenant_id) -> Evaluacion:
        """Crear convocatoria."""

    async def listar(self, tenant_id, filtros, es_admin=False) -> list[dict]:
        """Listar convocatorias. Si es ALUMNO, solo las de su cohorte."""

    async def detalle(self, id, tenant_id) -> dict:
        """Detalle + métricas: convocados, reservas activas, cupos libres."""

    async def importar_alumnos(self, id, alumno_ids, tenant_id) -> dict:
        """Registra alumnos habilitados para la convocatoria (Tabla AlumnoConvocatoria o lista en JSONB)."""
        # For simplicity: store alumno_ids in a JSONB field "convocados" on Evaluacion
        # or create a many-to-many table
        
    async def reservar(self, id, alumno_id, fecha, hora, tenant_id) -> ReservaEvaluacion:
        """Reservar turno. Valida: cupo disponible, no reserva duplicada, evaluación activa."""
        # 1. Check evaluacion activa
        # 2. Check alumno no tiene ya reserva
        # 3. Count reservas Activa for (evaluacion_id, fecha) < cupo_por_dia
        # 4. Create reserva

    async def cancelar_reserva(self, id, alumno_id, tenant_id) -> None:
        """Cancelar reserva (solo propia). estado → Cancelada."""

    async def registrar_resultado(self, evaluacion_id, alumno_id, nota, tenant_id) -> ResultadoEvaluacion:
        """Registrar nota final."""

    async def listar_reservas(self, evaluacion_id, tenant_id) -> list:
        """Ver reservas de una convocatoria."""

    async def admin_global(self, tenant_id) -> list:
        """Admin: todas las convocatorias con métricas."""
```

### Validation: cupo validation
```python
# On reservar:
activas = await self._count_reservas_activas(evaluacion_id, fecha)
if activas >= evaluacion.cupo_por_dia:
    raise ValueError("Cupo completo para esta fecha")
```

## Router

```python
router = APIRouter(prefix="/api/coloquios", tags=["coloquios"])

# COORDINADOR/ADMIN
@router.post("", status_code=201)  # coloquios:gestionar
@router.get("")  # coloquios:gestionar O alumno autenticado (solo su cohorte)
@router.get("/{id}")  # coloquios:gestionar
@router.post("/{id}/alumnos")  # coloquios:gestionar
@router.get("/{id}/reservas")  # coloquios:gestionar
@router.post("/{id}/resultados")  # coloquios:gestionar
@router.get("/{id}/resultados")  # coloquios:gestionar
@router.get("/admin")  # coloquios:gestionar + scope admin

# ALUMNO
@router.post("/{id}/reservar")  # cualquier rol autenticado
@router.patch("/reservas/{id}")  # ALUMNO (propia)
```

## Tests

- Crear convocatoria con cupo
- Reservar: resta cupo disponible
- Reservar: cupo completo rechaza
- Reservar: duplicado rechaza
- Cancelar reserva: propia OK, ajena 403
- Registrar resultado
- Métricas: convocados/reservas/cupos libres
- Multi-tenant isolation
- 403 sin permiso
