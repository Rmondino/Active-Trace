from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.repositories.user_repository import UserRepository
from app.repositories.version_padron_repository import VersionPadronRepository

__all__ = [
    "AsignacionRepository",
    "CalificacionRepository",
    "CarreraRepository",
    "ComunicacionRepository",
    "CohorteRepository",
    "EntradaPadronRepository",
    "MateriaRepository",
    "TenantRepository",
    "UmbralMateriaRepository",
    "UserRepository",
    "VersionPadronRepository",
]
