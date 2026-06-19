## Modelos

### Aviso
```python
class Aviso(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "aviso"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alcance: Mapped[str] = mapped_column(String(20), nullable=False)  # Global|PorMateria|PorCohorte|PorRol
    materia_id: Mapped[str | None] = mapped_column(ForeignKey("materia.id"), nullable=True)
    cohorte_id: Mapped[str | None] = mapped_column(ForeignKey("cohorte.id"), nullable=True)
    rol_destino: Mapped[str | None] = mapped_column(String(20), nullable=True)  # nullable = todos
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="Info")  # Info|Advertencia|Critico
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[str] = mapped_column(String(5000), nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
```

### AcknowledgmentAviso
```python
class AcknowledgmentAviso(Base, TimeStampedMixin, SoftDeleteMixin, TenantScopedMixin):
    __tablename__ = "acknowledgment_aviso"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    aviso_id: Mapped[str] = mapped_column(ForeignKey("aviso.id"), nullable=False, index=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuario.id"), nullable=False, index=True)
    confirmado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
```

Unique: `(tenant_id, aviso_id, usuario_id)` — un ack por usuario por aviso.

## Servicio

### AvisoService

```python
class AvisoService:
    async def crear(self, data, user_id, tenant_id) -> Aviso
    
    async def listar_visibles(self, usuario_id, tenant_id, roles: list[str], asignaciones: list[Asignacion]) -> list[dict]:
        """Filtra avisos según RN-20 y RN-18.
        - Solo activos dentro de vigencia (inicio_en <= now <= fin_en)
        - Según alcance: Global, PorMateria (materia_id en asignaciones), 
          PorCohorte (cohorte_id en asignaciones), PorRol (rol_destino en roles del user)
        - Ordenado por orden DESC
        - Si ya tiene ack y requiere_ack: igual se muestra pero con flag ackeado
        """
        avisos = await self.avisos_repo.get_activos_vigentes(tenant_id)
        visibles = []
        for aviso in avisos:
            if not self._es_visible(aviso, roles, asignaciones):
                continue
            tiene_ack = await self.ack_repo.has_ack(aviso.id, usuario_id)
            visibles.append({**aviso_dict, "ackeado": tiene_ack})
        return sorted(visibles, key=lambda a: a["orden"], reverse=True)
    
    def _es_visible(self, aviso: Aviso, roles: list[str], asignaciones: list[Asignacion]) -> bool:
        if aviso.alcance == "Global":
            return True
        if aviso.alcance == "PorMateria":
            return any(a.materia_id == aviso.materia_id for a in asignaciones if a.materia_id)
        if aviso.alcance == "PorCohorte":
            return any(a.cohorte_id == aviso.cohorte_id for a in asignaciones if a.cohorte_id)
        if aviso.alcance == "PorRol":
            return aviso.rol_destino in roles
        return False
    
    async def ack(self, aviso_id, usuario_id, tenant_id) -> dict
    async def stats(self, aviso_id, tenant_id) -> dict  # total_visibles, total_acks
```

## Router

```python
router = APIRouter(prefix="/api/avisos", tags=["avisos"])

@router.post("", status_code=201, dependencies=[Depends(require_permission("avisos:publicar"))])

@router.get("")  # any authenticated — filtered by scope
async def listar_avisos(..., current_user=Depends(get_current_user)):
    # Get user's roles and asignaciones from repos
    # Pass to AvisoService.listar_visibles()

@router.get("/{id}")  # any authenticated (if visible)

@router.put("/{id}", dependencies=[Depends(require_permission("avisos:publicar"))])

@router.delete("/{id}", dependencies=[Depends(require_permission("avisos:publicar"))])

@router.post("/{id}/ack", status_code=201)  # any authenticated

@router.get("/{id}/stats", dependencies=[Depends(require_permission("avisos:publicar"))])
```

## Tests

- Crear aviso con todos los campos
- Listar: Global visible para todos
- Listar: PorMateria visible solo si user tiene asignación
- Listar: PorCohorte filtrado
- Listar: PorRol filtrado
- Listar: fuera de vigencia no se muestra (RN-18)
- Ack: crear ack, stats reflejan
- Ack: duplicado rechazado (unique)
- Orden: descendente por orden
- 403 sin avisos:publicar en endpoints de gestión
- Multi-tenant isolation
