"""Tests for GuardiaService."""

import uuid
from datetime import date

import pytest

from app.models.asignacion import Asignacion
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.guardia_repository import GuardiaRepository
from app.services.guardia_service import GuardiaService


async def _seed_base(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"gua-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="gua", email_hash="h", password_hash="h",
        nombre="Carlos", apellidos="López", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()

    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="MAT-GUA", nombre="Programación I",
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


class TestRegistrarGuardia:
    async def test_registra_guardia(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        guardia = await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Lunes",
            "horario": "14:00-14:45",
        }, user_id=seed["user_id"])

        assert guardia.id is not None
        assert guardia.dia == "Lunes"
        assert guardia.horario == "14:00-14:45"
        assert guardia.estado == "Pendiente"

    async def test_registra_con_comentarios(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        guardia = await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Martes",
            "horario": "15:00-15:45",
            "comentarios": "Atención de consultas",
        }, user_id=seed["user_id"])

        assert guardia.comentarios == "Atención de consultas"


class TestListarGuardias:
    async def test_listar_por_materia(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Lunes", "horario": "14:00-14:45",
        }, user_id=seed["user_id"])
        await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Miércoles", "horario": "16:00-16:45",
        }, user_id=seed["user_id"])

        guardias = await svc.listar(seed["materia_id"])
        assert len(guardias) == 2

    async def test_listar_todas_sin_filtro(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Lunes", "horario": "14:00-14:45",
        }, user_id=seed["user_id"])

        guardias = await svc.listar()
        assert len(guardias) >= 1


class TestExportarGuardias:
    async def test_exportar_returns_xlsx(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Lunes", "horario": "14:00-14:45",
        }, user_id=seed["user_id"])

        content = await svc.exportar()
        assert isinstance(content, bytes)
        assert len(content) > 0
        assert content[:2] == b"PK"

    async def test_exportar_por_materia(self, db_session):
        seed = await _seed_base(db_session)
        repo = GuardiaRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = GuardiaService(db_session, repo, seed["tenant_id"])

        await svc.registrar({
            "asignacion_id": seed["asignacion_id"],
            "materia_id": seed["materia_id"],
            "dia": "Lunes", "horario": "14:00-14:45",
        }, user_id=seed["user_id"])

        content = await svc.exportar(seed["materia_id"])
        assert isinstance(content, bytes)
        assert len(content) > 0
