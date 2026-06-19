"""Usuarios me router — perfil propio y asignaciones del usuario autenticado.

Endpoints:
    - GET /api/usuarios/me — perfil completo con PII descifrada
    - PUT /api/usuarios/me — actualizar perfil propio
    - GET /api/usuarios/me/asignaciones — asignaciones activas del usuario
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import get_current_user
from app.core.dependencies import get_db
from app.core.security import decrypt, encrypt, get_encryption_key
from app.models.user import User

router = APIRouter(prefix="/api/usuarios", tags=["usuarios_me"])


class PerfilUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None


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


@router.get("/me", response_model=dict)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return _decrypt_user(current_user, get_encryption_key(settings))


@router.put("/me", response_model=dict)
async def update_me(
    request: PerfilUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    enc_key = get_encryption_key(settings)

    update_data = request.model_dump(exclude_none=True)

    for field in ["cbu", "alias_cbu"]:
        if field in update_data and update_data[field]:
            update_data[field] = encrypt(update_data[field], enc_key)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    await db.flush()
    await db.refresh(current_user)

    return _decrypt_user(current_user, enc_key)


@router.get("/me/asignaciones", response_model=list[dict])
async def get_me_asignaciones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    from app.repositories.asignacion_repository import AsignacionRepository
    from app.routers.asignaciones import _compute_estado_vigencia

    repo = AsignacionRepository(session=db, tenant_id=current_user.tenant_id)
    asignaciones = await repo.get_by_usuario(
        current_user.tenant_id, current_user.id, solo_vigentes=True
    )

    return [
        {
            "id": a.id,
            "usuario_id": a.usuario_id,
            "rol": a.rol,
            "materia_id": a.materia_id,
            "carrera_id": a.carrera_id,
            "cohorte_id": a.cohorte_id,
            "comisiones": a.comisiones,
            "responsable_id": a.responsable_id,
            "desde": str(a.desde),
            "hasta": str(a.hasta) if a.hasta else None,
            "estado_vigencia": _compute_estado_vigencia(a.desde, a.hasta),
        }
        for a in asignaciones
    ]
