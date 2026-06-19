"""Tests for CalificacionRepository and UmbralMateriaRepository."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.umbral_materia import UmbralMateria
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository


@pytest.fixture
async def seed_cal_data(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug="cal-repo", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-CAL-R", nombre="Test")
    db_session.add(materia)
    await db_session.flush()
    return {"tenant_id": tenant.id, "materia_id": materia.id}


class TestCalificacionRepository:
    async def test_create_and_get(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
            materia_id=seed_cal_data["materia_id"], actividad="Parcial 1",
            nota_numerica=Decimal("80"), origen="Importado", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        fetched = await repo.get(cal.id)
        assert fetched is not None
        assert fetched.actividad == "Parcial 1"
        assert fetched.nota_numerica == Decimal("80")

    async def test_get_by_materia(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        for i in range(3):
            cal = Calificacion(
                id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
                materia_id=seed_cal_data["materia_id"], actividad=f"Act{i}",
                nota_numerica=Decimal(str(60 + i * 10)), origen="Importado",
                aprobado=True,
            )
            db_session.add(cal)
        await db_session.flush()

        results = await repo.get_by_materia(seed_cal_data["materia_id"])
        assert len(results) == 3

    async def test_get_by_materia_other_tenant(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
            materia_id=seed_cal_data["materia_id"], actividad="Test",
            nota_numerica=Decimal("70"), origen="Importado", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        other_tenant_id = str(uuid.uuid4())
        other_repo = CalificacionRepository(session=db_session, tenant_id=other_tenant_id)
        results = await other_repo.get_by_materia(seed_cal_data["materia_id"])
        assert len(results) == 0

    async def test_get_by_materia_empty(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        results = await repo.get_by_materia(str(uuid.uuid4()))
        assert len(results) == 0

    async def test_get_by_entrada(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        from app.models.entrada_padron import EntradaPadron
        from app.models.version_padron import VersionPadron
        from app.models.user import User
        from app.models.cohorte import Cohorte
        from app.models.carrera import Carrera
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"], codigo="CARR", nombre="T")
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"], carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"], email="e@t.com", email_hash="h", password_hash="p", nombre="U", apellidos="T", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()
        vp = VersionPadron(id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"], materia_id=seed_cal_data["materia_id"], cohorte_id=cohorte.id, cargado_por=user.id, origen="manual", total_filas=1)
        db_session.add(vp)
        await db_session.flush()
        ep = EntradaPadron(id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"], version_id=vp.id, nombre="A", apellidos="B", email="e@t.com")
        db_session.add(ep)
        await db_session.flush()

        for i in range(2):
            cal = Calificacion(
                id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
                entrada_padron_id=ep.id, materia_id=seed_cal_data["materia_id"],
                actividad=f"Act{i}", nota_numerica=Decimal("70"),
                origen="Importado", aprobado=True,
            )
            db_session.add(cal)
        await db_session.flush()

        results = await repo.get_by_entrada(ep.id)
        assert len(results) == 2

    async def test_bulk_create(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        cals = [
            Calificacion(
                id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
                materia_id=seed_cal_data["materia_id"], actividad=f"Act{i}",
                nota_numerica=Decimal("75"), origen="Importado", aprobado=True,
            )
            for i in range(5)
        ]
        await repo.bulk_create(cals)

        results = await repo.get_by_materia(seed_cal_data["materia_id"])
        assert len(results) == 5

    async def test_get_actividades_by_materia(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        for name in ["Parcial 1", "TP Grupal", "Parcial 1"]:
            cal = Calificacion(
                id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
                materia_id=seed_cal_data["materia_id"], actividad=name,
                nota_numerica=Decimal("70"), origen="Importado", aprobado=True,
            )
            db_session.add(cal)
        await db_session.flush()

        actividades = await repo.get_actividades_by_materia(seed_cal_data["materia_id"])
        assert sorted(actividades) == sorted(["Parcial 1", "TP Grupal"])

    async def test_vaciar_materia(self, db_session, seed_cal_data):
        repo = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
            materia_id=seed_cal_data["materia_id"], actividad="Test",
            nota_numerica=Decimal("70"), origen="Importado", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        await repo.vaciar_materia(seed_cal_data["materia_id"])
        fetched = await repo.get(cal.id)
        assert fetched is None

    async def test_multi_tenant_isolation(self, db_session, seed_cal_data):
        repo_a = CalificacionRepository(session=db_session, tenant_id=seed_cal_data["tenant_id"])
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=seed_cal_data["tenant_id"],
            materia_id=seed_cal_data["materia_id"], actividad="Test",
            nota_numerica=Decimal("70"), origen="Importado", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        other_tenant = str(uuid.uuid4())
        repo_b = CalificacionRepository(session=db_session, tenant_id=other_tenant)
        results = await repo_b.get_by_materia(seed_cal_data["materia_id"])
        assert len(results) == 0


class TestUmbralMateriaRepository:
    @pytest.fixture
    async def seed_umbral_data(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug="umb-repo", nombre="Test", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        from app.models.user import User
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="u@t.com", email_hash="h", password_hash="p", nombre="U", apellidos="T", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()
        from app.models.asignacion import Asignacion
        from datetime import date
        asig = Asignacion(id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id, rol="PROFESOR", desde=date(2020, 1, 1))
        db_session.add(asig)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-UMB-R", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        return {"tenant_id": tenant.id, "asignacion_id": asig.id, "materia_id": materia.id}

    async def test_create_and_get(self, db_session, seed_umbral_data):
        repo = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=seed_umbral_data["tenant_id"],
            asignacion_id=seed_umbral_data["asignacion_id"],
            materia_id=seed_umbral_data["materia_id"],
            umbral_pct=70, valores_aprobatorios=["Aprobado"],
        )
        db_session.add(umbral)
        await db_session.flush()

        fetched = await repo.get_by_asignacion_materia(
            seed_umbral_data["asignacion_id"], seed_umbral_data["materia_id"]
        )
        assert fetched is not None
        assert fetched.umbral_pct == 70
        assert fetched.valores_aprobatorios == ["Aprobado"]

    async def test_get_by_asignacion_materia_none(self, db_session, seed_umbral_data):
        repo = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        result = await repo.get_by_asignacion_materia(
            seed_umbral_data["asignacion_id"], str(uuid.uuid4())
        )
        assert result is None

    async def test_upsert_create(self, db_session, seed_umbral_data):
        repo = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=seed_umbral_data["tenant_id"],
            asignacion_id=seed_umbral_data["asignacion_id"],
            materia_id=seed_umbral_data["materia_id"],
            umbral_pct=75, valores_aprobatorios=["Bueno", "Excelente"],
        )
        result = await repo.upsert(umbral)
        assert result.umbral_pct == 75
        assert result.valores_aprobatorios == ["Bueno", "Excelente"]

    async def test_upsert_update(self, db_session, seed_umbral_data):
        repo = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=seed_umbral_data["tenant_id"],
            asignacion_id=seed_umbral_data["asignacion_id"],
            materia_id=seed_umbral_data["materia_id"],
            umbral_pct=60,
        )
        await repo.upsert(umbral)

        umbral.umbral_pct = 85
        umbral.valores_aprobatorios = ["Sobresaliente"]
        result = await repo.upsert(umbral)
        assert result.umbral_pct == 85
        assert result.valores_aprobatorios == ["Sobresaliente"]

    async def test_get_default(self, db_session, seed_umbral_data):
        repo = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        default = await repo.get_default()
        assert default == 60

    async def test_get_default_valores(self):
        valores = UmbralMateriaRepository.get_default_valores_aprobatorios()
        assert valores == ["Satisfactorio", "Supera lo esperado"]

    async def test_multi_tenant_isolation(self, db_session, seed_umbral_data):
        repo_a = UmbralMateriaRepository(session=db_session, tenant_id=seed_umbral_data["tenant_id"])
        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=seed_umbral_data["tenant_id"],
            asignacion_id=seed_umbral_data["asignacion_id"],
            materia_id=seed_umbral_data["materia_id"],
            umbral_pct=60,
        )
        db_session.add(umbral)
        await db_session.flush()

        other_tenant = str(uuid.uuid4())
        repo_b = UmbralMateriaRepository(session=db_session, tenant_id=other_tenant)
        result = await repo_b.get_by_asignacion_materia(
            seed_umbral_data["asignacion_id"], seed_umbral_data["materia_id"]
        )
        assert result is None
