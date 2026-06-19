"""Tests for EncuentroService."""

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.materia import Materia
from app.models.slot_encuentro import SlotEncuentro
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.services.encuentro_service import EncuentroService


async def _seed_base(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"enc-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc", email_hash="h", password_hash="h",
        nombre="Carlos", apellidos="López", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()

    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="MAT-ENC", nombre="Programación I",
    )
    db_session.add(materia)
    await db_session.flush()

    asignacion = Asignacion(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        usuario_id=user.id, rol="PROFESOR",
        materia_id=materia.id, desde=date(2026, 1, 1),
    )
    db_session.add(asignacion)
    await db_session.flush()

    return {
        "tenant_id": tenant.id, "materia_id": materia.id,
        "asignacion_id": asignacion.id, "user_id": user.id,
    }


class TestCrearSlot:
    async def test_recurrente_genera_instancias(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        result = await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "Clase Semanal",
            "hora": "18:00",
            "dia_semana": "Lunes",
            "fecha_inicio": date(2026, 3, 2),
            "cant_semanas": 4,
            "vig_desde": date(2026, 3, 1),
            "vig_hasta": date(2026, 4, 1),
        }, user_id=seed["user_id"])

        assert result["slot"].cant_semanas == 4
        assert len(result["instancias"]) == 4
        assert result["instancias"][0].fecha == date(2026, 3, 2)
        assert result["instancias"][1].fecha == date(2026, 3, 9)
        assert result["instancias"][2].fecha == date(2026, 3, 16)
        assert result["instancias"][3].fecha == date(2026, 3, 23)

    async def test_unico_genera_una_instancia(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        result = await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "Clase Única",
            "hora": "18:00",
            "cant_semanas": 0,
            "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1),
            "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        assert result["slot"].cant_semanas == 0
        assert len(result["instancias"]) == 1
        assert result["instancias"][0].fecha == date(2026, 3, 15)

    async def test_error_si_recurrente_sin_dia_semana(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        with pytest.raises(Exception) as exc:
            await svc.crear_slot({
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "Mal",
                "hora": "18:00",
                "cant_semanas": 4,
                "vig_desde": date(2026, 3, 1),
                "vig_hasta": date(2026, 4, 1),
            }, user_id=seed["user_id"])
        assert "requiere dia_semana" in str(exc.value)

    async def test_error_si_unico_sin_fecha_unica(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        with pytest.raises(Exception) as exc:
            await svc.crear_slot({
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "Mal",
                "hora": "18:00",
                "cant_semanas": 0,
                "vig_desde": date(2026, 3, 1),
                "vig_hasta": date(2026, 4, 1),
            }, user_id=seed["user_id"])
        assert "requiere fecha_unica" in str(exc.value)

    async def test_error_si_recurrente_con_fecha_unica(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        with pytest.raises(Exception) as exc:
            await svc.crear_slot({
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "Mal",
                "hora": "18:00",
                "dia_semana": "Lunes",
                "fecha_inicio": date(2026, 3, 2),
                "cant_semanas": 4,
                "fecha_unica": date(2026, 3, 15),
                "vig_desde": date(2026, 3, 1),
                "vig_hasta": date(2026, 4, 1),
            }, user_id=seed["user_id"])
        assert "no puede tener fecha_unica" in str(exc.value)


class TestEditarInstancia:
    async def test_editar_instancia_no_afecta_slot(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        result = await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "Clase",
            "hora": "18:00",
            "cant_semanas": 0,
            "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1),
            "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        instancia = result["instancias"][0]
        slot_id = result["slot"].id

        updated = await svc.editar_instancia(instancia.id, {
            "estado": "Realizado",
            "video_url": "https://video.example.com",
            "comentario": "Buena clase",
        })
        assert updated.estado == "Realizado"
        assert updated.video_url == "https://video.example.com"

        slot = await slot_repo.get(slot_id)
        assert slot.titulo == "Clase"

    async def test_editar_instancia_independiente_entre_instancias(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        result = await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "Clase Semanal",
            "hora": "18:00",
            "dia_semana": "Lunes",
            "fecha_inicio": date(2026, 3, 2),
            "cant_semanas": 2,
            "vig_desde": date(2026, 3, 1),
            "vig_hasta": date(2026, 4, 1),
        }, user_id=seed["user_id"])

        inst1 = result["instancias"][0]
        inst2 = result["instancias"][1]

        await svc.editar_instancia(inst1.id, {"estado": "Realizado"})

        stmt = select(InstanciaEncuentro).where(InstanciaEncuentro.id == inst2.id)
        i2 = (await db_session.execute(stmt)).scalar_one()
        assert i2.estado == "Programado"


class TestListar:
    async def test_listar_slots_por_materia(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "C1", "hora": "18:00",
            "cant_semanas": 0, "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        slots = await svc.listar_slots(seed["materia_id"])
        assert len(slots) == 1
        assert slots[0].titulo == "C1"

    async def test_listar_instancias_por_materia(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "C1", "hora": "18:00",
            "cant_semanas": 3, "dia_semana": "Lunes",
            "fecha_inicio": date(2026, 3, 2),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 4, 1),
        }, user_id=seed["user_id"])

        instancias = await svc.listar_instancias(seed["materia_id"])
        assert len(instancias) == 3


class TestContenidoAula:
    async def test_genera_html_con_tabla(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "C1", "hora": "18:00",
            "cant_semanas": 0, "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        html = await svc.generar_contenido_aula(seed["materia_id"])
        assert "<table>" in html
        assert "<th>Fecha</th>" in html
        assert "<th>Estado</th>" in html
        assert "2026-03-15" in html
        assert "Programado" in html


class TestVistaAdmin:
    async def test_retorna_todos_los_encuentros(self, db_session):
        seed = await _seed_base(db_session)
        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "Admin Test", "hora": "18:00",
            "cant_semanas": 0, "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        data = await svc.vista_admin()
        assert len(data) == 1
        assert data[0]["slot"]["titulo"] == "Admin Test"
        assert len(data[0]["instancias"]) == 1

    async def test_filtra_por_materia(self, db_session):
        seed = await _seed_base(db_session)
        materia2 = Materia(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            codigo="MAT-ENC2", nombre="Otra",
        )
        db_session.add(materia2)
        await db_session.flush()

        slot_repo = SlotEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        inst_repo = InstanciaEncuentroRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = EncuentroService(db_session, slot_repo, inst_repo, seed["tenant_id"])

        await svc.crear_slot({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "titulo": "M1", "hora": "18:00",
            "cant_semanas": 0, "fecha_unica": date(2026, 3, 15),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        asignacion2 = Asignacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            usuario_id=seed["user_id"], rol="PROFESOR",
            materia_id=materia2.id, desde=date(2026, 1, 1),
        )
        db_session.add(asignacion2)
        await db_session.flush()

        await svc.crear_slot({
            "asignacion_id": asignacion2.id,
            "materia_id": materia2.id,
            "titulo": "M2", "hora": "19:00",
            "cant_semanas": 0, "fecha_unica": date(2026, 3, 16),
            "vig_desde": date(2026, 3, 1), "vig_hasta": date(2026, 3, 31),
        }, user_id=seed["user_id"])

        data = await svc.vista_admin(filtros={"materia_id": seed["materia_id"]})
        assert len(data) == 1
        assert data[0]["slot"]["titulo"] == "M1"
