"""Estructura académica router — ABM de carreras, cohortes y materias.

All endpoints require `estructura:gestionar` permission (ADMIN role).
Multi-tenant isolation via BaseRepository tenant filtering.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.current_user import get_current_user
from app.models.user import User
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository

router = APIRouter(prefix="/api/admin", tags=["estructura"])

# ── Schemas ──


class CarreraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str


class CarreraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None
    estado: str | None = None


class CarreraResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    codigo: str
    nombre: str
    estado: str
    tenant_id: str


class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    carrera_id: str
    nombre: str
    anio: int
    vig_desde: str
    vig_hasta: str | None = None


class CohorteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None
    anio: int | None = None
    vig_desde: str | None = None
    vig_hasta: str | None = None
    estado: str | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    carrera_id: str
    nombre: str
    anio: int
    vig_desde: str
    vig_hasta: str | None
    estado: str
    tenant_id: str


class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str
    nombre: str


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = None
    estado: str | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    codigo: str
    nombre: str
    estado: str
    tenant_id: str


# ── Dependencies ──


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


# ── Carreras ──


@router.get("/carreras", response_model=list[CarreraResponse])
async def list_carreras(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CarreraRepository(session=db, tenant_id=tenant_id)
    carreras = await repo.list()
    return [
        CarreraResponse(
            id=c.id, codigo=c.codigo, nombre=c.nombre,
            estado=c.estado, tenant_id=c.tenant_id,
        )
        for c in carreras
    ]


@router.get("/carreras/{carrera_id}", response_model=CarreraResponse)
async def get_carrera(
    carrera_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CarreraRepository(session=db, tenant_id=tenant_id)
    carrera = await repo.get(carrera_id)
    if carrera is None:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return CarreraResponse(
        id=carrera.id, codigo=carrera.codigo, nombre=carrera.nombre,
        estado=carrera.estado, tenant_id=carrera.tenant_id,
    )


@router.post("/carreras", response_model=CarreraResponse, status_code=201)
async def create_carrera(
    body: CarreraCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CarreraRepository(session=db, tenant_id=tenant_id)
    if await repo.exists_by_codigo(body.codigo):
        raise HTTPException(status_code=409, detail="El código de carrera ya existe")
    carrera = await repo.create(body.model_dump())
    return CarreraResponse(
        id=carrera.id, codigo=carrera.codigo, nombre=carrera.nombre,
        estado=carrera.estado, tenant_id=carrera.tenant_id,
    )


@router.put("/carreras/{carrera_id}", response_model=CarreraResponse)
async def update_carrera(
    carrera_id: str,
    body: CarreraUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CarreraRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    carrera = await repo.update(carrera_id, data)
    if carrera is None:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return CarreraResponse(
        id=carrera.id, codigo=carrera.codigo, nombre=carrera.nombre,
        estado=carrera.estado, tenant_id=carrera.tenant_id,
    )


@router.delete("/carreras/{carrera_id}", status_code=204)
async def delete_carrera(
    carrera_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CarreraRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(carrera_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return None


# ── Cohortes ──


@router.get("/cohortes", response_model=list[CohorteResponse])
async def list_cohortes(
    carrera_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CohorteRepository(session=db, tenant_id=tenant_id)
    filters = {}
    if carrera_id:
        filters["carrera_id"] = carrera_id
    cohortes = await repo.list(**filters)
    return [
        CohorteResponse(
            id=c.id, carrera_id=c.carrera_id, nombre=c.nombre,
            anio=c.anio, vig_desde=c.vig_desde, vig_hasta=c.vig_hasta,
            estado=c.estado, tenant_id=c.tenant_id,
        )
        for c in cohortes
    ]


@router.get("/cohortes/{cohorte_id}", response_model=CohorteResponse)
async def get_cohorte(
    cohorte_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CohorteRepository(session=db, tenant_id=tenant_id)
    cohorte = await repo.get(cohorte_id)
    if cohorte is None:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada")
    return CohorteResponse(
        id=cohorte.id, carrera_id=cohorte.carrera_id, nombre=cohorte.nombre,
        anio=cohorte.anio, vig_desde=cohorte.vig_desde, vig_hasta=cohorte.vig_hasta,
        estado=cohorte.estado, tenant_id=cohorte.tenant_id,
    )


@router.post("/cohortes", response_model=CohorteResponse, status_code=201)
async def create_cohorte(
    body: CohorteCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CohorteRepository(session=db, tenant_id=tenant_id)
    if await repo.exists_by_nombre_y_carrera(body.nombre, body.carrera_id):
        raise HTTPException(status_code=409, detail="El nombre de cohorte ya existe para esta carrera")
    try:
        cohorte = await repo.create(body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CohorteResponse(
        id=cohorte.id, carrera_id=cohorte.carrera_id, nombre=cohorte.nombre,
        anio=cohorte.anio, vig_desde=cohorte.vig_desde, vig_hasta=cohorte.vig_hasta,
        estado=cohorte.estado, tenant_id=cohorte.tenant_id,
    )


@router.put("/cohortes/{cohorte_id}", response_model=CohorteResponse)
async def update_cohorte(
    cohorte_id: str,
    body: CohorteUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CohorteRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    cohorte = await repo.update(cohorte_id, data)
    if cohorte is None:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada")
    return CohorteResponse(
        id=cohorte.id, carrera_id=cohorte.carrera_id, nombre=cohorte.nombre,
        anio=cohorte.anio, vig_desde=cohorte.vig_desde, vig_hasta=cohorte.vig_hasta,
        estado=cohorte.estado, tenant_id=cohorte.tenant_id,
    )


@router.delete("/cohortes/{cohorte_id}", status_code=204)
async def delete_cohorte(
    cohorte_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = CohorteRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(cohorte_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada")
    return None


# ── Materias ──


@router.get("/materias", response_model=list[MateriaResponse])
async def list_materias(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaRepository(session=db, tenant_id=tenant_id)
    materias = await repo.list()
    return [
        MateriaResponse(
            id=m.id, codigo=m.codigo, nombre=m.nombre,
            estado=m.estado, tenant_id=m.tenant_id,
        )
        for m in materias
    ]


@router.get("/materias/{materia_id}", response_model=MateriaResponse)
async def get_materia(
    materia_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaRepository(session=db, tenant_id=tenant_id)
    materia = await repo.get(materia_id)
    if materia is None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return MateriaResponse(
        id=materia.id, codigo=materia.codigo, nombre=materia.nombre,
        estado=materia.estado, tenant_id=materia.tenant_id,
    )


@router.post("/materias", response_model=MateriaResponse, status_code=201)
async def create_materia(
    body: MateriaCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaRepository(session=db, tenant_id=tenant_id)
    if await repo.exists_by_codigo(body.codigo):
        raise HTTPException(status_code=409, detail="El código de materia ya existe")
    materia = await repo.create(body.model_dump())
    return MateriaResponse(
        id=materia.id, codigo=materia.codigo, nombre=materia.nombre,
        estado=materia.estado, tenant_id=materia.tenant_id,
    )


@router.put("/materias/{materia_id}", response_model=MateriaResponse)
async def update_materia(
    materia_id: str,
    body: MateriaUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    materia = await repo.update(materia_id, data)
    if materia is None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return MateriaResponse(
        id=materia.id, codigo=materia.codigo, nombre=materia.nombre,
        estado=materia.estado, tenant_id=materia.tenant_id,
    )


@router.delete("/materias/{materia_id}", status_code=204)
async def delete_materia(
    materia_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(materia_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return None
