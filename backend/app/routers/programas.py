"""Programas router — ABM de programas de materia.

All endpoints require `estructura:gestionar` permission.
Multi-tenant isolation via BaseRepository tenant filtering.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.current_user import get_current_user
from app.models.user import User
from app.repositories.materia_repository import MateriaRepository
from app.repositories.programa_repository import ProgramaMateriaRepository

router = APIRouter(prefix="/api/programas", tags=["programas"])


class ProgramaMateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: str
    carrera_id: str
    cohorte_id: str
    titulo: str
    referencia_archivo: str


class ProgramaMateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str | None = None
    referencia_archivo: str | None = None


class ProgramaMateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    materia_id: str
    carrera_id: str
    cohorte_id: str
    titulo: str
    referencia_archivo: str
    cargado_at: datetime
    tenant_id: str


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.get("", response_model=list[ProgramaMateriaResponse])
async def list_programas(
    materia_id: str | None = Query(default=None),
    carrera_id: str | None = Query(default=None),
    cohorte_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    filters: dict[str, Any] = {}
    if materia_id:
        filters["materia_id"] = materia_id
    if carrera_id:
        filters["carrera_id"] = carrera_id
    if cohorte_id:
        filters["cohorte_id"] = cohorte_id
    programas = await repo.list(**filters)
    return [
        ProgramaMateriaResponse(
            id=p.id, materia_id=p.materia_id, carrera_id=p.carrera_id,
            cohorte_id=p.cohorte_id, titulo=p.titulo,
            referencia_archivo=p.referencia_archivo,
            cargado_at=p.cargado_at, tenant_id=p.tenant_id,
        )
        for p in programas
    ]


@router.get("/{programa_id}", response_model=ProgramaMateriaResponse)
async def get_programa(
    programa_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    programa = await repo.get(programa_id)
    if programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return ProgramaMateriaResponse(
        id=programa.id, materia_id=programa.materia_id,
        carrera_id=programa.carrera_id, cohorte_id=programa.cohorte_id,
        titulo=programa.titulo, referencia_archivo=programa.referencia_archivo,
        cargado_at=programa.cargado_at, tenant_id=programa.tenant_id,
    )


@router.post("", response_model=ProgramaMateriaResponse, status_code=201)
async def create_programa(
    body: ProgramaMateriaCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    if await repo.exists_by_materia_carrera_cohorte(
        body.materia_id, body.carrera_id, body.cohorte_id,
    ):
        raise HTTPException(
            status_code=409,
            detail="Ya existe un programa para esta materia, carrera y cohorte",
        )
    data = body.model_dump()
    data.setdefault("cargado_at", datetime.now(UTC))
    programa = await repo.create(data)
    return ProgramaMateriaResponse(
        id=programa.id, materia_id=programa.materia_id,
        carrera_id=programa.carrera_id, cohorte_id=programa.cohorte_id,
        titulo=programa.titulo, referencia_archivo=programa.referencia_archivo,
        cargado_at=programa.cargado_at, tenant_id=programa.tenant_id,
    )


@router.put("/{programa_id}", response_model=ProgramaMateriaResponse)
async def update_programa(
    programa_id: str,
    body: ProgramaMateriaUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    programa = await repo.update(programa_id, data)
    if programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return ProgramaMateriaResponse(
        id=programa.id, materia_id=programa.materia_id,
        carrera_id=programa.carrera_id, cohorte_id=programa.cohorte_id,
        titulo=programa.titulo, referencia_archivo=programa.referencia_archivo,
        cargado_at=programa.cargado_at, tenant_id=programa.tenant_id,
    )


@router.delete("/{programa_id}", status_code=204)
async def delete_programa(
    programa_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(programa_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return None


@router.post("/contenido-lms")
async def contenido_lms_programas(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = ProgramaMateriaRepository(session=db, tenant_id=tenant_id)
    programas = await repo.list()
    items_html = "".join(
        f"<li>{p.titulo}</li>" for p in programas
    )
    html = f"<h3>Programas</h3><ul>{items_html}</ul>" if programas else "<h3>Programas</h3><p>Sin programas cargados</p>"
    return {"html": html}
