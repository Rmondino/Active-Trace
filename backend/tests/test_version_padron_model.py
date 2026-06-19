"""Tests for VersionPadron and EntradaPadron models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.entrada_padron import EntradaPadron
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.models.version_padron import VersionPadron


async def _seed_base(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug="test-m", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR01", nombre="Test")
    db_session.add(carrera)
    await db_session.flush()
    return tenant, carrera


class TestVersionPadronModel:
    async def test_create_version_padron(self, db_session):
        tenant, carrera = await _seed_base(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT001", nombre="Matematicas")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="test@test.com", email_hash="hash", password_hash="hash", nombre="Test", apellidos="User", dni="encrypted", estado="Activo")
        db_session.add(user)
        await db_session.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=10,
        )
        db_session.add(vp)
        await db_session.flush()

        result = await db_session.execute(select(VersionPadron).where(VersionPadron.id == vp.id))
        fetched = result.scalar_one()
        assert fetched.id == vp.id
        assert fetched.materia_id == materia.id
        assert fetched.cohorte_id == cohorte.id
        assert fetched.cargado_por == user.id
        assert fetched.origen == "manual"
        assert fetched.activa is True
        assert fetched.total_filas == 10

    async def test_version_padron_default_activa_true(self, db_session):
        tenant, carrera = await _seed_base(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT002", nombre="Fisica")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026B", anio=2026, vig_desde="2026-06-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="t2@test.com", email_hash="hash2", password_hash="hash", nombre="T", apellidos="U", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="moodle", total_filas=5,
        )
        db_session.add(vp)
        await db_session.flush()
        assert vp.activa is True

    async def test_version_padron_soft_delete(self, db_session):
        tenant, carrera = await _seed_base(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT003", nombre="Quimica")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026C", anio=2026, vig_desde="2026-03-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="t3@test.com", email_hash="hash3", password_hash="hash", nombre="T", apellidos="U", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=3,
        )
        db_session.add(vp)
        await db_session.flush()

        vp.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(VersionPadron).where(VersionPadron.id == vp.id, VersionPadron.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None


class TestEntradaPadronModel:
    async def test_create_entrada_padron(self, db_session):
        tenant, carrera = await _seed_base(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT010", nombre="Historia")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026D", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="t4@test.com", email_hash="hash4", password_hash="hash", nombre="T", apellidos="U", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=1,
        )
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            version_id=vp.id, usuario_id=user.id,
            nombre="Juan", apellidos="Perez",
            email="encrypted_email", comision="A", regional="CABA",
        )
        db_session.add(ep)
        await db_session.flush()

        result = await db_session.execute(select(EntradaPadron).where(EntradaPadron.id == ep.id))
        fetched = result.scalar_one()
        assert fetched.id == ep.id
        assert fetched.version_id == vp.id
        assert fetched.usuario_id == user.id
        assert fetched.nombre == "Juan"
        assert fetched.apellidos == "Perez"
        assert fetched.comision == "A"
        assert fetched.regional == "CABA"

    async def test_entrada_padron_sin_usuario(self, db_session):
        tenant, carrera = await _seed_base(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT011", nombre="Geografia")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026E", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="t5@test.com", email_hash="hash5", password_hash="hash", nombre="T", apellidos="U", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=1,
        )
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            version_id=vp.id, usuario_id=None,
            nombre="Sin", apellidos="Cuenta",
            email="encrypted_email2",
        )
        db_session.add(ep)
        await db_session.flush()

        result = await db_session.execute(select(EntradaPadron).where(EntradaPadron.id == ep.id))
        fetched = result.scalar_one()
        assert fetched.usuario_id is None
