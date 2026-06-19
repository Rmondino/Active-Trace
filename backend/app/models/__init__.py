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
from app.models.version_padron import VersionPadron
from app.models.entrada_padron import EntradaPadron
from app.models.audit_log import AuditLog

__all__ = [
    "Asignacion",
    "AuditLog",
    "Carrera",
    "Cohorte",
    "EntradaPadron",
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
    "VersionPadron",
]
