"""Domain models for activia-trace.

All domain models inherit from Base (core/database.py) plus mixins.
"""

from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin
from app.models.password_reset_token import PasswordResetToken
from app.models.permiso import Permiso
from app.models.refresh_token import RefreshToken
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.asignacion import Asignacion

__all__ = [
    "Asignacion",
    "Carrera",
    "Cohorte",
    "Materia",
    "PasswordResetToken",
    "Permiso",
    "RefreshToken",
    "Rol",
    "RolPermiso",
    "SoftDeleteMixin",
    "Tenant",
    "TenantScopedMixin",
    "TimeStampedMixin",
    "User",
]
