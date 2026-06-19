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
from app.models.calificacion import Calificacion
from app.models.comunicacion import Comunicacion
from app.models.umbral_materia import UmbralMateria
from app.models.slot_encuentro import SlotEncuentro
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.guardia import Guardia
from app.models.aviso import Aviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.evaluacion import Evaluacion
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.tarea import Tarea, validar_transicion_tarea, VALID_TRANSITIONS_TAREA
from app.models.comentario_tarea import ComentarioTarea
from app.models.liquidacion import (
    SalarioBase,
    SalarioPlus,
    MateriaGrupoPlus,
    Liquidacion,
    Factura,
)

__all__ = [
    "Asignacion",
    "AuditLog",
    "Calificacion",
    "Comunicacion",
    "Carrera",
    "Cohorte",
    "EntradaPadron",
    "Materia",
    "UmbralMateria",
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
    "SlotEncuentro",
    "InstanciaEncuentro",
    "Guardia",
    "Evaluacion",
    "ReservaEvaluacion",
    "ResultadoEvaluacion",
    "Aviso",
    "AcknowledgmentAviso",
    "Tarea",
    "ComentarioTarea",
    "validar_transicion_tarea",
    "VALID_TRANSITIONS_TAREA",
    "SalarioBase",
    "SalarioPlus",
    "MateriaGrupoPlus",
    "Liquidacion",
    "Factura",
]
