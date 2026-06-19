"""Salarios router — CRUD para salario base, plus y grupos materia.

Endpoints:
    - GET/POST /api/salarios/bases
    - GET/PUT/DELETE /api/salarios/bases/{id}
    - GET/POST /api/salarios/plus
    - GET/PUT/DELETE /api/salarios/plus/{id}
    - GET/POST /api/salarios/grupos-materia
    - GET/PUT/DELETE /api/salarios/grupos-materia/{id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.salario_repository import (
    MateriaGrupoPlusRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.schemas.liquidacion import (
    MateriaGrupoPlusCreate,
    MateriaGrupoPlusResponse,
    MateriaGrupoPlusUpdate,
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)

router = APIRouter(prefix="/api/salarios", tags=["salarios"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


# ── SalarioBase ──


@router.get("/bases", response_model=list[SalarioBaseResponse])
async def list_bases(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioBaseRepository(session=db, tenant_id=tenant_id)
    bases = await repo.list()
    return [
        SalarioBaseResponse(
            id=b.id, tenant_id=b.tenant_id, rol=b.rol, monto=float(b.monto),
            desde=b.desde, hasta=b.hasta,
            created_at=b.created_at, updated_at=b.updated_at,
        )
        for b in bases
    ]


@router.post("/bases", response_model=SalarioBaseResponse, status_code=201)
async def create_base(
    body: SalarioBaseCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioBaseRepository(session=db, tenant_id=tenant_id)
    base = await repo.create(body.model_dump())
    return SalarioBaseResponse(
        id=base.id, tenant_id=base.tenant_id, rol=base.rol, monto=float(base.monto),
        desde=base.desde, hasta=base.hasta,
        created_at=base.created_at, updated_at=base.updated_at,
    )


@router.get("/bases/{base_id}", response_model=SalarioBaseResponse)
async def get_base(
    base_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioBaseRepository(session=db, tenant_id=tenant_id)
    base = await repo.get(base_id)
    if base is None:
        raise HTTPException(status_code=404, detail="Salario base no encontrado")
    return SalarioBaseResponse(
        id=base.id, tenant_id=base.tenant_id, rol=base.rol, monto=float(base.monto),
        desde=base.desde, hasta=base.hasta,
        created_at=base.created_at, updated_at=base.updated_at,
    )


@router.put("/bases/{base_id}", response_model=SalarioBaseResponse)
async def update_base(
    base_id: str,
    body: SalarioBaseUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioBaseRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    base = await repo.update(base_id, data)
    if base is None:
        raise HTTPException(status_code=404, detail="Salario base no encontrado")
    return SalarioBaseResponse(
        id=base.id, tenant_id=base.tenant_id, rol=base.rol, monto=float(base.monto),
        desde=base.desde, hasta=base.hasta,
        created_at=base.created_at, updated_at=base.updated_at,
    )


@router.delete("/bases/{base_id}", status_code=204)
async def delete_base(
    base_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioBaseRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(base_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Salario base no encontrado")
    return None


# ── SalarioPlus ──


@router.get("/plus", response_model=list[SalarioPlusResponse])
async def list_plus(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioPlusRepository(session=db, tenant_id=tenant_id)
    plus_list = await repo.list()
    return [
        SalarioPlusResponse(
            id=p.id, tenant_id=p.tenant_id, grupo=p.grupo, rol=p.rol,
            descripcion=p.descripcion, monto=float(p.monto),
            desde=p.desde, hasta=p.hasta, tope_acumulacion=p.tope_acumulacion,
            created_at=p.created_at, updated_at=p.updated_at,
        )
        for p in plus_list
    ]


@router.post("/plus", response_model=SalarioPlusResponse, status_code=201)
async def create_plus(
    body: SalarioPlusCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioPlusRepository(session=db, tenant_id=tenant_id)
    plus = await repo.create(body.model_dump())
    return SalarioPlusResponse(
        id=plus.id, tenant_id=plus.tenant_id, grupo=plus.grupo, rol=plus.rol,
        descripcion=plus.descripcion, monto=float(plus.monto),
        desde=plus.desde, hasta=plus.hasta,
        tope_acumulacion=plus.tope_acumulacion,
        created_at=plus.created_at, updated_at=plus.updated_at,
    )


@router.get("/plus/{plus_id}", response_model=SalarioPlusResponse)
async def get_plus(
    plus_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioPlusRepository(session=db, tenant_id=tenant_id)
    plus = await repo.get(plus_id)
    if plus is None:
        raise HTTPException(status_code=404, detail="Salario plus no encontrado")
    return SalarioPlusResponse(
        id=plus.id, tenant_id=plus.tenant_id, grupo=plus.grupo, rol=plus.rol,
        descripcion=plus.descripcion, monto=float(plus.monto),
        desde=plus.desde, hasta=plus.hasta,
        tope_acumulacion=plus.tope_acumulacion,
        created_at=plus.created_at, updated_at=plus.updated_at,
    )


@router.put("/plus/{plus_id}", response_model=SalarioPlusResponse)
async def update_plus(
    plus_id: str,
    body: SalarioPlusUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioPlusRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    plus = await repo.update(plus_id, data)
    if plus is None:
        raise HTTPException(status_code=404, detail="Salario plus no encontrado")
    return SalarioPlusResponse(
        id=plus.id, tenant_id=plus.tenant_id, grupo=plus.grupo, rol=plus.rol,
        descripcion=plus.descripcion, monto=float(plus.monto),
        desde=plus.desde, hasta=plus.hasta,
        tope_acumulacion=plus.tope_acumulacion,
        created_at=plus.created_at, updated_at=plus.updated_at,
    )


@router.delete("/plus/{plus_id}", status_code=204)
async def delete_plus(
    plus_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = SalarioPlusRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(plus_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Salario plus no encontrado")
    return None


# ── MateriaGrupoPlus ──


@router.get("/grupos-materia", response_model=list[MateriaGrupoPlusResponse])
async def list_grupos_materia(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaGrupoPlusRepository(session=db, tenant_id=tenant_id)
    grupos = await repo.list()
    return [
        MateriaGrupoPlusResponse(
            id=g.id, tenant_id=g.tenant_id, materia_id=g.materia_id,
            grupo=g.grupo, desde=g.desde, hasta=g.hasta,
            created_at=g.created_at, updated_at=g.updated_at,
        )
        for g in grupos
    ]


@router.post("/grupos-materia", response_model=MateriaGrupoPlusResponse, status_code=201)
async def create_grupo_materia(
    body: MateriaGrupoPlusCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaGrupoPlusRepository(session=db, tenant_id=tenant_id)
    grupo = await repo.create(body.model_dump())
    return MateriaGrupoPlusResponse(
        id=grupo.id, tenant_id=grupo.tenant_id, materia_id=grupo.materia_id,
        grupo=grupo.grupo, desde=grupo.desde, hasta=grupo.hasta,
        created_at=grupo.created_at, updated_at=grupo.updated_at,
    )


@router.get("/grupos-materia/{grupo_id}", response_model=MateriaGrupoPlusResponse)
async def get_grupo_materia(
    grupo_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaGrupoPlusRepository(session=db, tenant_id=tenant_id)
    grupo = await repo.get(grupo_id)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo materia no encontrado")
    return MateriaGrupoPlusResponse(
        id=grupo.id, tenant_id=grupo.tenant_id, materia_id=grupo.materia_id,
        grupo=grupo.grupo, desde=grupo.desde, hasta=grupo.hasta,
        created_at=grupo.created_at, updated_at=grupo.updated_at,
    )


@router.put("/grupos-materia/{grupo_id}", response_model=MateriaGrupoPlusResponse)
async def update_grupo_materia(
    grupo_id: str,
    body: MateriaGrupoPlusUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaGrupoPlusRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    grupo = await repo.update(grupo_id, data)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo materia no encontrado")
    return MateriaGrupoPlusResponse(
        id=grupo.id, tenant_id=grupo.tenant_id, materia_id=grupo.materia_id,
        grupo=grupo.grupo, desde=grupo.desde, hasta=grupo.hasta,
        created_at=grupo.created_at, updated_at=grupo.updated_at,
    )


@router.delete("/grupos-materia/{grupo_id}", status_code=204)
async def delete_grupo_materia(
    grupo_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = MateriaGrupoPlusRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(grupo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Grupo materia no encontrado")
    return None
