"""FastAPI dependency guard for RBAC permission checking.

Provides:
    - require_permission: factory that returns a dependency checking a specific permission
    - Supports alcance `propio` vs `global` via optional owner_check
"""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request

from app.core.current_user import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.services.permission_service import PermissionService


def require_permission(
    codigo: str,
    owner_check: Callable[[Request, User], bool] | None = None,
) -> Callable[..., None]:
    """FastAPI dependency factory: require a specific permission.

    Usage:
        @router.get("/entregas")
        async def list_entregas(
            _: None = Depends(require_permission("entregas:ver")),
        ):
            ...

    For `propio` scoped permissions with an ownership check:
        @router.get("/entregas/{id}")
        async def get_entrega(
            _: None = Depends(require_permission(
                "entregas:ver",
                owner_check=lambda req, user: _es_su_entrega(req, user),
            )),
        ):
            ...

    Args:
        codigo: Permission code in `modulo:accion` format.
        owner_check: Optional callable (request, user) -> bool
                     for validating ownership of the target resource.

    Returns:
        A FastAPI dependency callable.
    """

    async def _dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
        db=Depends(get_db_session),
    ) -> None:
        ps = PermissionService(db)
        has_perm = await ps.has_permission(current_user, codigo)
        if not has_perm:
            raise HTTPException(
                status_code=403,
                detail=f"Permiso requerido: {codigo}",
            )

        # Check scope
        scope = await ps.get_permission_scope(current_user, codigo)
        if scope == "propio" and owner_check is not None:
            if not owner_check(request, current_user):
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso sobre este recurso",
                )
        elif scope == "propio" and owner_check is None:
            raise HTTPException(
                status_code=403,
                detail=f"El permiso {codigo} requiere verificación de Propio",
            )
        # scope == "global" → pass through regardless of owner_check

    return _dependency
