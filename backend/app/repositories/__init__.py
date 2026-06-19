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
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.guardia_repository import GuardiaRepository
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.resultado_repository import ResultadoRepository
from app.repositories.tarea_repository import TareaRepository
from app.repositories.comentario_repository import ComentarioRepository

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
    "SlotEncuentroRepository",
    "InstanciaEncuentroRepository",
    "GuardiaRepository",
    "EvaluacionRepository",
    "ReservaRepository",
    "ResultadoRepository",
    "TareaRepository",
    "ComentarioRepository",
]
