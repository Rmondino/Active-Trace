"""Admin usuarios router — CRUD de usuarios con PII cifrada.

All endpoints require `usuarios:gestionar` permission.
PII fields are encrypted at rest and masked in list responses.
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dependencies import get_db, require_permission
from app.core.current_user import get_current_user
from app.core.security import decrypt, encrypt, get_encryption_key, mask_email, mask_pii
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["usuarios"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _decrypt_user(user: User, enc_key: bytes) -> dict:
    return {
        "id": user.id,
        "nombre": user.nombre,
        "apellidos": user.apellidos,
        "email": decrypt(user.email, enc_key) if user.email else "",
        "dni": decrypt(user.dni, enc_key) if user.dni else "",
        "cuil": decrypt(user.cuil, enc_key) if user.cuil else None,
        "cbu": decrypt(user.cbu, enc_key) if user.cbu else None,
        "alias_cbu": decrypt(user.alias_cbu, enc_key) if user.alias_cbu else None,
        "banco": user.banco,
        "regional": user.regional,
        "legajo": user.legajo,
        "legajo_profesional": user.legajo_profesional,
        "facturador": user.facturador,
        "estado": user.estado,
    }


@router.post("/usuarios", response_model=dict, status_code=201)
async def create_usuario(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate

    data = UserCreate(**body)
    repo = UserRepository(session=db, tenant_id=tenant_id)
    enc_key = get_encryption_key(settings)

    email_hash = hashlib.sha256(data.email.lower().encode("utf-8")).hexdigest()
    if await repo.exists_by_email_hash(tenant_id, email_hash):
        raise HTTPException(status_code=409, detail="El email ya existe en este tenant")

    user = await repo.create({
        "email": encrypt(data.email, enc_key),
        "email_hash": email_hash,
        "password_hash": "",
        "nombre": data.nombre,
        "apellidos": data.apellidos,
        "dni": encrypt(data.dni, enc_key),
        "cuil": encrypt(data.cuil, enc_key) if data.cuil else None,
        "cbu": encrypt(data.cbu, enc_key) if data.cbu else None,
        "alias_cbu": encrypt(data.alias_cbu, enc_key) if data.alias_cbu else None,
        "banco": data.banco,
        "regional": data.regional,
        "legajo": data.legajo,
        "legajo_profesional": data.legajo_profesional,
        "facturador": data.facturador or False,
        "estado": "Activo",
    })

    return _decrypt_user(user, enc_key)


@router.get("/usuarios", response_model=list[dict])
async def list_usuarios(
    search: str | None = None,
    estado: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(session=db, tenant_id=tenant_id)
    enc_key = get_encryption_key(settings)

    if search:
        users = await repo.search(tenant_id, search)
    else:
        filters = {}
        if estado:
            filters["estado"] = estado
        users = await repo.list(**filters)

    result = []
    for u in users:
        email_plain = decrypt(u.email, enc_key) if u.email else ""
        result.append({
            "id": u.id,
            "nombre": u.nombre,
            "apellidos": u.apellidos,
            "email": mask_email(email_plain),
            "dni": mask_pii(decrypt(u.dni, enc_key)) if u.dni else None,
            "legajo": u.legajo,
            "regional": u.regional,
            "estado": u.estado,
            "facturador": u.facturador,
        })
    return result


@router.get("/usuarios/{usuario_id}", response_model=dict)
async def get_usuario(
    usuario_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(session=db, tenant_id=tenant_id)
    user = await repo.get(usuario_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return _decrypt_user(user, get_encryption_key(settings))


@router.put("/usuarios/{usuario_id}", response_model=dict)
async def update_usuario(
    usuario_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserUpdate

    data = UserUpdate(**body)
    repo = UserRepository(session=db, tenant_id=tenant_id)
    user = await repo.get(usuario_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    enc_key = get_encryption_key(settings)

    update_data = {}
    if data.nombre is not None:
        update_data["nombre"] = data.nombre
    if data.apellidos is not None:
        update_data["apellidos"] = data.apellidos
    if data.email is not None:
        email_hash = hashlib.sha256(data.email.lower().encode("utf-8")).hexdigest()
        if await repo.exists_by_email_hash(tenant_id, email_hash, exclude_id=usuario_id):
            raise HTTPException(status_code=409, detail="El email ya existe en este tenant")
        update_data["email"] = encrypt(data.email, enc_key)
        update_data["email_hash"] = email_hash
    if data.dni is not None:
        update_data["dni"] = encrypt(data.dni, enc_key)
    if data.cuil is not None:
        update_data["cuil"] = encrypt(data.cuil, enc_key)
    if data.cbu is not None:
        update_data["cbu"] = encrypt(data.cbu, enc_key)
    if data.alias_cbu is not None:
        update_data["alias_cbu"] = encrypt(data.alias_cbu, enc_key)
    for field in ("banco", "regional", "legajo", "legajo_profesional", "estado"):
        val = getattr(data, field, None)
        if val is not None:
            update_data[field] = val
    if data.facturador is not None:
        update_data["facturador"] = data.facturador

    updated = await repo.update(usuario_id, update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return _decrypt_user(updated, enc_key)


@router.delete("/usuarios/{usuario_id}", status_code=204)
async def delete_usuario(
    usuario_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("usuarios:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(usuario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None
