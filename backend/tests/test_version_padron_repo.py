"""Tests for VersionPadronRepository and EntradaPadronRepository."""

import uuid

import pytest

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.entrada_padron import EntradaPadron
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.models.version_padron import VersionPadron
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.version_padron_repository import VersionPadronRepository


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug="test-repo", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="REPOCARR", nombre="Repo Test")
    db_session.add(carrera)
    await db_session.flush()
    materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT100", nombre="Test")
    db_session.add(materia)
    await db_session.flush()
    cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
    db_session.add(cohorte)
    await db_session.flush()
    user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="r@test.com", email_hash="rhash", password_hash="hash", nombre="R", apellidos="Tester", dni="e", estado="Activo")
    db_session.add(user)
    await db_session.flush()

    return {
        "tenant_id": tenant.id,
        "materia_id": materia.id,
        "cohorte_id": cohorte.id,
        "user_id": user.id,
    }


class TestVersionPadronRepository:
    async def test_create_and_get(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo.create({
            "id": str(uuid.uuid4()),
            "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"],
            "cargado_por": seed_data["user_id"],
            "origen": "manual",
            "total_filas": 5,
        })
        assert vp.id is not None
        assert vp.activa is True
        fetched = await repo.get(vp.id)
        assert fetched is not None
        assert fetched.origen == "manual"

    async def test_get_activa_returns_active(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp1 = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 5, "activa": False,
        })
        vp2 = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "moodle", "total_filas": 3, "activa": True,
        })
        activa = await repo.get_activa(seed_data["materia_id"], seed_data["cohorte_id"])
        assert activa is not None
        assert activa.id == vp2.id
        assert activa.origen == "moodle"

    async def test_get_activa_returns_none_when_no_active(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        result = await repo.get_activa(seed_data["materia_id"], seed_data["cohorte_id"])
        assert result is None

    async def test_desactivar_anteriores(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp1 = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 5, "activa": True,
        })
        vp2 = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 3, "activa": True,
        })
        await repo.desactivar_anteriores(seed_data["materia_id"], seed_data["cohorte_id"], except_id=vp2.id)

        vp1_fetched = await repo.get(vp1.id)
        vp2_fetched = await repo.get(vp2.id)
        assert vp1_fetched.activa is False
        assert vp2_fetched.activa is True

    async def test_desactivar_anteriores_all(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp1 = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 5, "activa": True,
        })
        await repo.desactivar_anteriores(seed_data["materia_id"], seed_data["cohorte_id"], except_id=None)
        vp1_fetched = await repo.get(vp1.id)
        assert vp1_fetched.activa is False

    async def test_list_by_materia(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 1,
        })
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "moodle", "total_filas": 2,
        })
        versiones = await repo.list_by_materia(seed_data["materia_id"])
        assert len(versiones) == 2

    async def test_list_by_materia_empty(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        versiones = await repo.list_by_materia(str(uuid.uuid4()))
        assert len(versiones) == 0

    async def test_vaciar_materia(self, db_session, seed_data):
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 5,
        })
        await repo.vaciar_materia(seed_data["materia_id"])
        fetched = await repo.get(vp.id)
        assert fetched is None

    async def test_multi_tenant_isolation(self, db_session, seed_data):
        other_tenant_id = str(uuid.uuid4())
        repo = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 5,
        })
        other_repo = VersionPadronRepository(session=db_session, tenant_id=other_tenant_id)
        versiones = await other_repo.list_by_materia(seed_data["materia_id"])
        assert len(versiones) == 0


class TestEntradaPadronRepository:
    async def test_create_and_get(self, db_session, seed_data):
        repo_ver = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo_ver.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 1,
        })
        repo = EntradaPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            version_id=vp.id, nombre="A", apellidos="B", email="enc_email",
        )
        db_session.add(ep)
        await db_session.flush()
        entries = await repo.get_by_version(vp.id)
        assert len(entries) == 1

    async def test_bulk_create(self, db_session, seed_data):
        repo_ver = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo_ver.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 3,
        })
        repo = EntradaPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        entradas = [
            EntradaPadron(id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
                          version_id=vp.id, nombre=f"N{i}", apellidos="A", email=f"e{i}@t.com")
            for i in range(3)
        ]
        await repo.bulk_create(entradas)
        entries = await repo.get_by_version(vp.id)
        assert len(entries) == 3

    async def test_count_by_version(self, db_session, seed_data):
        repo_ver = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo_ver.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 0,
        })
        repo = EntradaPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        entradas = [
            EntradaPadron(id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
                          version_id=vp.id, nombre="N", apellidos="A", email=f"e{i}@t.com")
            for i in range(2)
        ]
        await repo.bulk_create(entradas)
        count = await repo.count_by_version(vp.id)
        assert count == 2

    async def test_vaciar_by_version(self, db_session, seed_data):
        repo_ver = VersionPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        vp = await repo_ver.create({
            "id": str(uuid.uuid4()), "materia_id": seed_data["materia_id"],
            "cohorte_id": seed_data["cohorte_id"], "cargado_por": seed_data["user_id"],
            "origen": "manual", "total_filas": 1,
        })
        repo = EntradaPadronRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            version_id=vp.id, nombre="X", apellidos="Y", email="e@t.com",
        )
        db_session.add(ep)
        await db_session.flush()
        await repo.vaciar_by_version(vp.id)
        entries = await repo.get_by_version(vp.id)
        assert len(entries) == 0
