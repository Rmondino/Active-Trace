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

__all__ = [
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
