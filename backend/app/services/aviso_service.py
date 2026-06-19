"""AvisoService — manage notices, visibility filtering (RN-18, RN-20), and acknowledgment."""

import logging
import uuid

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.repositories.ack_repository import AckRepository
from app.repositories.aviso_repository import AvisoRepository

logger = logging.getLogger(__name__)


class AvisoService:

    def __init__(
        self,
        aviso_repo: AvisoRepository,
        ack_repo: AckRepository,
        session: AsyncSession,
    ) -> None:
        self.aviso_repo = aviso_repo
        self.ack_repo = ack_repo
        self.session = session

    async def crear(self, data: dict, tenant_id: str) -> Aviso:
        """Create a new notice."""
        return await self.aviso_repo.create(data)

    async def actualizar(self, id: str, data: dict, tenant_id: str) -> Aviso | None:
        """Update an existing notice."""
        return await self.aviso_repo.update(id, data)

    async def eliminar(self, id: str, tenant_id: str) -> None:
        """Soft-delete a notice."""
        await self.aviso_repo.soft_delete(id)

    async def listar_visibles(
        self,
        usuario_id: str,
        tenant_id: str,
        roles: list[str],
        asignaciones: list,
    ) -> list[dict]:
        """List visible notices for a user.

        Filters by scope (RN-20) and vigencia (RN-18).
        Sorted by orden DESC (higher = more priority).

        Args:
            usuario_id: The user UUID.
            tenant_id: The tenant UUID.
            roles: List of role slugs for the user.
            asignaciones: List of Asignacion instances for the user.

        Returns:
            List of dicts with notice data and ackeado flag.
        """
        avisos = await self.aviso_repo.get_activos_vigentes(tenant_id)
        visibles = []
        for a in avisos:
            if not self._es_visible(a, roles, asignaciones):
                continue
            ackeado = await self.ack_repo.has_ack(a.id, usuario_id)
            visibles.append(self._to_dict(a, ackeado=ackeado))
        return sorted(visibles, key=lambda x: x["orden"], reverse=True)

    def _es_visible(self, aviso: Aviso, roles: list[str], asignaciones: list) -> bool:
        """Check if a notice is visible for the given roles and asignaciones (RN-20)."""
        if aviso.alcance == "Global":
            return True
        if aviso.alcance == "PorMateria" and aviso.materia_id:
            return any(
                getattr(a, "materia_id", None) == aviso.materia_id
                for a in asignaciones
            )
        if aviso.alcance == "PorCohorte" and aviso.cohorte_id:
            return any(
                getattr(a, "cohorte_id", None) == aviso.cohorte_id
                for a in asignaciones
            )
        if aviso.alcance == "PorRol" and aviso.rol_destino:
            return aviso.rol_destino in roles
        return False

    async def ack(self, aviso_id: str, usuario_id: str, tenant_id: str) -> AcknowledgmentAviso:
        """Record a user acknowledgment for a notice.

        Raises ValueError if already acknowledged.
        """
        exists = await self.ack_repo.has_ack(aviso_id, usuario_id)
        if exists:
            raise ValueError("Ya has acusado recibo de este aviso")

        ack = AcknowledgmentAviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            aviso_id=aviso_id,
            usuario_id=usuario_id,
        )
        self.session.add(ack)
        await self.session.flush()
        return ack

    async def stats(self, aviso_id: str, tenant_id: str) -> dict:
        """Get acknowledgment statistics for a notice."""
        count = await self.ack_repo.count_by_aviso(aviso_id)
        return {"total_acks": count}

    def _to_dict(self, a: Aviso, ackeado: bool = False) -> dict:
        """Convert an Aviso instance to a serializable dict."""
        return {
            "id": a.id,
            "tenant_id": a.tenant_id,
            "alcance": a.alcance,
            "materia_id": a.materia_id,
            "cohorte_id": a.cohorte_id,
            "rol_destino": a.rol_destino,
            "severidad": a.severidad,
            "titulo": a.titulo,
            "cuerpo": a.cuerpo,
            "inicio_en": a.inicio_en.isoformat() if a.inicio_en else None,
            "fin_en": a.fin_en.isoformat() if a.fin_en else None,
            "orden": a.orden,
            "activo": a.activo,
            "requiere_ack": a.requiere_ack,
            "ackeado": ackeado,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
