"""ComunicacionService — preview, enqueue, approval, and state machine."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from app.core.crypto import CipherService
from app.models.comunicacion import Comunicacion
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger(__name__)

# ── State machine ──

VALID_TRANSITIONS: dict[str, set[str]] = {
    "Pendiente": {"Enviando", "Cancelado"},
    "Enviando": {"Enviado", "Error"},
}


def validar_transicion(actual: str, nuevo: str) -> None:
    if actual not in VALID_TRANSITIONS:
        raise ValueError(
            f"Estado terminal '{actual}': no permite transiciones"
        )
    if nuevo not in VALID_TRANSITIONS[actual]:
        raise ValueError(
            f"Transición inválida: {actual} → {nuevo}"
        )


# ── Preview store ──

_preview_store: dict[str, dict] = {}
PREVIEW_TTL = timedelta(minutes=30)


def _store_preview(data: dict) -> str:
    token = str(uuid.uuid4())
    _preview_store[token] = {
        **data,
        "created_at": datetime.now(UTC),
        "used": False,
    }
    return token


def _get_and_validate_preview(token: str) -> dict:
    entry = _preview_store.get(token)
    if entry is None:
        raise ValueError("Preview no encontrado")
    if entry.get("used"):
        raise ValueError("Preview ya utilizado")
    if datetime.now(UTC) - entry["created_at"] > PREVIEW_TTL:
        raise ValueError("Preview expirado")
    return entry


# ── Template variables ──

TEMPLATE_VARS = {
    "{alumno_nombre}",
    "{alumno_apellidos}",
    "{materia}",
    "{comision}",
}


def _render_template(template: str, vars_map: dict[str, str]) -> str:
    result = template
    for key, value in vars_map.items():
        result = result.replace(key, value)
    return result


# ── Service ──


class ComunicacionService:

    def __init__(
        self,
        repo: ComunicacionRepository,
        materia_repo: MateriaRepository,
        tenant_repo: TenantRepository,
        cipher: CipherService,
        audit: AuditLogService,
    ) -> None:
        self.repo = repo
        self.materia_repo = materia_repo
        self.tenant_repo = tenant_repo
        self.cipher = cipher
        self.audit = audit

    async def generar_preview(
        self,
        materia_id: str,
        asunto_template: str,
        cuerpo_template: str,
        alumnos: list[dict],
        tenant_id: str,
    ) -> dict:
        materia = await self.materia_repo.get(materia_id)
        materia_nombre = materia.nombre if materia else ""

        previews = []
        for alumno in alumnos:
            vars_map = {
                "{alumno_nombre}": alumno.get("nombre", ""),
                "{alumno_apellidos}": alumno.get("apellidos", ""),
                "{materia}": materia_nombre,
                "{comision}": alumno.get("comision", ""),
            }
            previews.append({
                "alumno_id": alumno.get("id", ""),
                "alumno_nombre": f"{alumno.get('nombre', '')} {alumno.get('apellidos', '')}".strip(),
                "asunto": _render_template(asunto_template, vars_map),
                "cuerpo": _render_template(cuerpo_template, vars_map),
            })

        token = _store_preview({
            "materia_id": materia_id,
            "asunto_template": asunto_template,
            "cuerpo_template": cuerpo_template,
            "alumnos": alumnos,
            "tenant_id": tenant_id,
        })

        return {
            "previews": previews,
            "preview_token": token,
        }

    async def encolar(
        self,
        materia_id: str,
        asunto: str,
        cuerpo: str,
        destinatarios: list[dict],
        user_id: str,
        tenant_id: str,
        preview_token: str | None = None,
    ) -> dict:
        if not preview_token:
            raise ValueError("Preview requerido")

        preview = _get_and_validate_preview(preview_token)
        if preview["materia_id"] != materia_id:
            raise ValueError("Materia no coincide con preview")
        if preview["tenant_id"] != tenant_id:
            raise ValueError("Tenant no coincide con preview")

        preview["used"] = True

        tenant = await self.tenant_repo.get(tenant_id)
        config = tenant.config or {} if tenant else {}
        requiere_aprobacion = config.get("aprobacion_requerida", False)

        lote_id = str(uuid.uuid4())
        comunicaciones = []
        for dest in destinatarios:
            email_encrypted = self.cipher.encrypt(dest["email"])
            com = Comunicacion(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                enviado_por=user_id,
                materia_id=materia_id,
                destinatario=email_encrypted,
                asunto=asunto,
                cuerpo=cuerpo,
                estado="Pendiente",
                lote_id=lote_id,
            )
            comunicaciones.append(com)

        await self.repo.bulk_create(comunicaciones)

        await self.audit.log(
            actor_id=user_id,
            tenant_id=tenant_id,
            accion="COMUNICACION_ENVIAR",
            materia_id=materia_id,
            detalle={
                "lote_id": lote_id,
                "total": len(destinatarios),
                "requiere_aprobacion": requiere_aprobacion,
            },
        )

        return {
            "lote_id": lote_id,
            "total": len(destinatarios),
            "requiere_aprobacion": requiere_aprobacion,
        }

    async def aprobar_lote(
        self,
        lote_id: str,
        aprobador_id: str,
        tenant_id: str,
    ) -> dict:
        mensajes = await self.repo.get_by_lote(lote_id)
        ahora = datetime.now(UTC)
        count = 0
        for msg in mensajes:
            if msg.estado == "Pendiente" and msg.aprobado_por is None:
                msg.aprobado_por = aprobador_id
                msg.aprobado_at = ahora
                count += 1
        if count:
            await self.repo.session.flush()

        await self.audit.log(
            actor_id=aprobador_id,
            tenant_id=tenant_id,
            accion="COMUNICACION_APROBAR",
            materia_id=mensajes[0].materia_id if mensajes else None,
            detalle={"lote_id": lote_id, "aprobados": count},
        )

        return {"aprobados": count}

    async def aprobar(
        self,
        comunicacion_id: str,
        aprobador_id: str,
        tenant_id: str,
    ) -> dict:
        msg = await self.repo.get(comunicacion_id)
        if msg is None:
            raise ValueError("Comunicación no encontrada")
        if msg.estado != "Pendiente":
            raise ValueError(f"No se puede aprobar un mensaje en estado '{msg.estado}'")
        msg.aprobado_por = aprobador_id
        msg.aprobado_at = datetime.now(UTC)
        await self.repo.session.flush()

        await self.audit.log(
            actor_id=aprobador_id,
            tenant_id=tenant_id,
            accion="COMUNICACION_APROBAR",
            materia_id=msg.materia_id,
            detalle={"comunicacion_id": comunicacion_id, "estado": "Pendiente"},
        )

        return {"estado": "Pendiente"}

    async def rechazar(
        self,
        comunicacion_id: str,
        tenant_id: str,
        user_id: str | None = None,
    ) -> dict:
        msg = await self.repo.get(comunicacion_id)
        if msg is None:
            raise ValueError("Comunicación no encontrada")
        validar_transicion(msg.estado, "Cancelado")
        msg.estado = "Cancelado"
        await self.repo.session.flush()

        if user_id:
            await self.audit.log(
                actor_id=user_id,
                tenant_id=tenant_id,
                accion="COMUNICACION_RECHAZAR",
                materia_id=msg.materia_id,
                detalle={"comunicacion_id": comunicacion_id},
            )

        return {"estado": "Cancelado"}

    async def tracking(
        self,
        materia_id: str,
        tenant_id: str,
    ) -> list[dict]:
        mensajes = await self.repo.get_by_materia(materia_id)
        result = []
        for msg in mensajes:
            result.append({
                "id": msg.id,
                "destinatario_mask": self.cipher.mask(msg.destinatario)
                if hasattr(self.cipher, "mask")
                else "***",
                "asunto": msg.asunto,
                "estado": msg.estado,
                "lote_id": msg.lote_id,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "enviado_at": msg.enviado_at.isoformat() if msg.enviado_at else None,
                "error_msg": msg.error_msg,
            })
        return result

    async def get_pendientes_aprobacion(
        self,
        tenant_id: str,
    ) -> list[dict]:
        mensajes = await self.repo.get_pendientes_aprobacion()
        agrupados: dict[str, dict] = {}
        for msg in mensajes:
            if msg.lote_id not in agrupados:
                agrupados[msg.lote_id] = {
                    "lote_id": msg.lote_id,
                    "materia_id": msg.materia_id,
                    "count": 0,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
            agrupados[msg.lote_id]["count"] += 1
        return list(agrupados.values())
