"""EncuentroService — gestión de slots, instancias, contenido aula, vista admin."""

import logging
import uuid

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro

logger = logging.getLogger(__name__)


def _parse_date_value(value: date | str | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    parts = value.split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


class EncuentroService:

    def __init__(self, session, slot_repo, instancia_repo, tenant_id: str) -> None:
        self.session = session
        self.slot_repo = slot_repo
        self.instancia_repo = instancia_repo
        self.tenant_id = tenant_id

    async def crear_slot(self, data: dict, user_id: str) -> dict:
        cant_semanas = data.get("cant_semanas", 0)
        fecha_inicio = _parse_date_value(data.get("fecha_inicio"))
        fecha_unica = _parse_date_value(data.get("fecha_unica"))
        vig_desde = _parse_date_value(data["vig_desde"])
        vig_hasta = _parse_date_value(data["vig_hasta"])

        if cant_semanas and cant_semanas > 0:
            if not data.get("dia_semana") or not fecha_inicio:
                raise HTTPException(
                    status_code=400,
                    detail="Slot recurrente requiere dia_semana y fecha_inicio",
                )
            if fecha_unica:
                raise HTTPException(
                    status_code=400,
                    detail="Slot recurrente no puede tener fecha_unica",
                )
        else:
            if not fecha_unica:
                raise HTTPException(
                    status_code=400,
                    detail="Slot único requiere fecha_unica",
                )

        slot = SlotEncuentro(
            id=str(uuid.uuid4()),
            asignacion_id=data["asignacion_id"],
            materia_id=data["materia_id"],
            titulo=data["titulo"],
            hora=data["hora"],
            dia_semana=data.get("dia_semana"),
            fecha_inicio=fecha_inicio,
            cant_semanas=cant_semanas,
            fecha_unica=fecha_unica,
            meet_url=data.get("meet_url"),
            vig_desde=vig_desde,
            vig_hasta=vig_hasta,
            tenant_id=self.tenant_id,
        )
        self.session.add(slot)
        await self.session.flush()

        instancias = []
        if cant_semanas and cant_semanas > 0:
            for i in range(cant_semanas):
                fecha = fecha_inicio + timedelta(weeks=i)
                instancia = InstanciaEncuentro(
                    id=str(uuid.uuid4()),
                    slot_id=slot.id,
                    materia_id=data["materia_id"],
                    fecha=fecha,
                    hora=data["hora"],
                    titulo=data["titulo"],
                    estado="Programado",
                    meet_url=data.get("meet_url"),
                    tenant_id=self.tenant_id,
                )
                instancias.append(instancia)
        else:
            instancia = InstanciaEncuentro(
                id=str(uuid.uuid4()),
                slot_id=slot.id,
                materia_id=data["materia_id"],
                fecha=fecha_unica,
                hora=data["hora"],
                titulo=data["titulo"],
                estado="Programado",
                meet_url=data.get("meet_url"),
                tenant_id=self.tenant_id,
            )
            instancias.append(instancia)

        self.session.add_all(instancias)
        await self.session.flush()

        return {"slot": slot, "instancias": instancias}

    async def editar_instancia(self, id: str, data: dict) -> InstanciaEncuentro:
        instancia = await self.instancia_repo.get(id)
        if not instancia:
            raise HTTPException(status_code=404, detail="Instancia no encontrada")
        for key in ("estado", "meet_url", "video_url", "comentario"):
            if key in data:
                setattr(instancia, key, data[key])
        await self.session.flush()
        return instancia

    async def listar_slots(self, materia_id: str) -> list[SlotEncuentro]:
        return await self.slot_repo.get_by_materia(materia_id)

    async def listar_instancias(self, materia_id: str) -> list[InstanciaEncuentro]:
        return await self.instancia_repo.get_by_materia(materia_id)

    async def generar_contenido_aula(self, materia_id: str) -> str:
        instancias = await self.instancia_repo.get_by_materia(materia_id)
        rows_html = ""
        for inst in instancias:
            enlace = f'<a href="{inst.meet_url}">{inst.meet_url}</a>' if inst.meet_url else ""
            rows_html += (
                f"<tr>"
                f"<td>{inst.fecha.isoformat()}</td>"
                f"<td>{inst.hora}</td>"
                f"<td>{inst.titulo}</td>"
                f"<td>{enlace}</td>"
                f"<td>{inst.estado}</td>"
                f"</tr>"
            )
        return f"<table><tr><th>Fecha</th><th>Hora</th><th>Título</th><th>Enlace</th><th>Estado</th></tr>{rows_html}</table>"

    async def vista_admin(self, filtros: dict | None = None) -> list[dict]:
        stmt = select(SlotEncuentro).where(
            SlotEncuentro.tenant_id == self.tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        if filtros and filtros.get("materia_id"):
            stmt = stmt.where(SlotEncuentro.materia_id == filtros["materia_id"])
        stmt = stmt.order_by(SlotEncuentro.created_at.desc())
        result = await self.session.execute(stmt)
        slots = list(result.scalars().all())

        output = []
        for s in slots:
            instancias = await self.instancia_repo.list(
                slot_id=s.id,
            )
            output.append({
                "slot": {
                    "id": s.id,
                    "titulo": s.titulo,
                    "hora": s.hora,
                    "materia_id": s.materia_id,
                    "dia_semana": s.dia_semana,
                    "fecha_inicio": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
                    "cant_semanas": s.cant_semanas,
                    "fecha_unica": s.fecha_unica.isoformat() if s.fecha_unica else None,
                    "vig_desde": s.vig_desde.isoformat(),
                    "vig_hasta": s.vig_hasta.isoformat(),
                },
                "instancias": [
                    {
                        "id": i.id,
                        "fecha": i.fecha.isoformat(),
                        "hora": i.hora,
                        "titulo": i.titulo,
                        "estado": i.estado,
                        "meet_url": i.meet_url,
                    }
                    for i in instancias
                ],
            })
        return output

    async def get_slot_detalle(self, id: str) -> dict | None:
        slot = await self.slot_repo.get(id)
        if not slot:
            return None
        instancias = await self.instancia_repo.get_by_slot(id)
        return {
            "slot": {
                "id": slot.id,
                "asignacion_id": slot.asignacion_id,
                "materia_id": slot.materia_id,
                "titulo": slot.titulo,
                "hora": slot.hora,
                "dia_semana": slot.dia_semana,
                "fecha_inicio": slot.fecha_inicio.isoformat() if slot.fecha_inicio else None,
                "cant_semanas": slot.cant_semanas,
                "fecha_unica": slot.fecha_unica.isoformat() if slot.fecha_unica else None,
                "meet_url": slot.meet_url,
                "vig_desde": slot.vig_desde.isoformat(),
                "vig_hasta": slot.vig_hasta.isoformat(),
            },
            "instancias": [
                {
                    "id": i.id,
                    "fecha": i.fecha.isoformat(),
                    "hora": i.hora,
                    "titulo": i.titulo,
                    "estado": i.estado,
                    "meet_url": i.meet_url,
                    "video_url": i.video_url,
                    "comentario": i.comentario,
                }
                for i in instancias
            ],
        }
