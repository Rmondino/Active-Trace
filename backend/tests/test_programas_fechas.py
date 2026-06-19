"""Tests for C-17 Programas y Fechas Academicas (modelos, repositorios, router, multi-tenant).
"""

import uuid
from datetime import UTC, date, datetime

import pytest
import sqlalchemy.exc
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


async def _seed_role_permiso(
    db: AsyncSession, slug: str, codigo: str, alcance: str = "global"
) -> None:
    """Upsert a direct role↔permission assignment for testing."""
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    result = await db.execute(select(Rol).where(Rol.slug == slug))
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db.add(role)
        await db.flush()

    result = await db.execute(select(Permiso).where(Permiso.codigo == codigo))
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(
            id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}"
        )
        db.add(permiso)
        await db.flush()

    result = await db.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id
        )
    )
    if result.scalar_one_or_none():
        return

    rp = RolPermiso(
        id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance
    )
    db.add(rp)
    await db.flush()


async def _create_tenant(db: AsyncSession) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


async def _seed_materia(db, tenant_id, codigo="PROG_I"):
    from app.models.materia import Materia
    m = Materia(id=str(uuid.uuid4()), tenant_id=tenant_id, codigo=codigo, nombre="Programacion I")
    db.add(m)
    await db.flush()
    return m


async def _seed_carrera(db, tenant_id, codigo="TUPAD"):
    from app.models.carrera import Carrera
    c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant_id, codigo=codigo, nombre="Tecnicatura")
    db.add(c)
    await db.flush()
    return c


async def _seed_cohorte(db, tenant_id, carrera_id, nombre="MAR-2026"):
    from app.models.cohorte import Cohorte
    ch = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant_id, carrera_id=carrera_id, nombre=nombre, anio=2026, vig_desde="2026-03-01")
    db.add(ch)
    await db.flush()
    return ch


# ═══════════════════════════════════════════════════════
# 1. Tests de modelos
# ═══════════════════════════════════════════════════════


class TestProgramaMateriaModel:
    """Model creation and constraints for ProgramaMateria."""

    async def test_create_programa(self, db_session: AsyncSession):
        from app.models.programa_materia import ProgramaMateria

        tenant = await _create_tenant(db_session)
        materia = await _seed_materia(db_session, tenant.id)
        carrera = await _seed_carrera(db_session, tenant.id)
        cohorte = await _seed_cohorte(db_session, tenant.id, carrera.id)

        programa = ProgramaMateria(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            titulo="Programa Analítico 2026",
            referencia_archivo="programa_v1.pdf",
        )
        db_session.add(programa)
        await db_session.flush()
        assert programa.id is not None
        assert programa.titulo == "Programa Analítico 2026"
        assert programa.referencia_archivo == "programa_v1.pdf"
        assert programa.materia_id == materia.id
        assert programa.carrera_id == carrera.id
        assert programa.cohorte_id == cohorte.id
        assert programa.deleted_at is None
        assert programa.tenant_id == tenant.id
        assert programa.cargado_at is not None

    async def test_programa_unique_constraint(self, db_session: AsyncSession):
        from app.models.programa_materia import ProgramaMateria

        tenant = await _create_tenant(db_session)
        materia = await _seed_materia(db_session, tenant.id)
        carrera = await _seed_carrera(db_session, tenant.id)
        cohorte = await _seed_cohorte(db_session, tenant.id, carrera.id)

        p1 = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Original", referencia_archivo="v1.pdf",
        )
        p2 = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Duplicado", referencia_archivo="v2.pdf",
        )
        db_session.add_all([p1, p2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_programa_tenant_isolation(self, db_session: AsyncSession):
        from app.models.programa_materia import ProgramaMateria

        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        m1 = await _seed_materia(db_session, t1.id, "M1")
        m2 = await _seed_materia(db_session, t2.id, "M2")
        c1 = await _seed_carrera(db_session, t1.id)
        c2 = await _seed_carrera(db_session, t2.id)
        ch1 = await _seed_cohorte(db_session, t1.id, c1.id)
        ch2 = await _seed_cohorte(db_session, t2.id, c2.id)

        p1 = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=t1.id,
            materia_id=m1.id, carrera_id=c1.id, cohorte_id=ch1.id,
            titulo="T1", referencia_archivo="t1.pdf",
        )
        p2 = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=t2.id,
            materia_id=m2.id, carrera_id=c2.id, cohorte_id=ch2.id,
            titulo="T2", referencia_archivo="t2.pdf",
        )
        db_session.add_all([p1, p2])
        await db_session.flush()

        result = await db_session.execute(
            select(ProgramaMateria).where(ProgramaMateria.tenant_id == t1.id, ProgramaMateria.deleted_at.is_(None))
        )
        t1_programas = list(result.scalars().all())
        assert len(t1_programas) == 1
        assert t1_programas[0].titulo == "T1"


class TestFechaAcademicaModel:
    """Model creation and constraints for FechaAcademica."""

    async def test_create_fecha(self, db_session: AsyncSession):
        from app.models.fecha_academica import FechaAcademica

        tenant = await _create_tenant(db_session)
        materia = await _seed_materia(db_session, tenant.id)
        carrera = await _seed_carrera(db_session, tenant.id)
        cohorte = await _seed_cohorte(db_session, tenant.id, carrera.id)

        fa = FechaAcademica(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo="Parcial",
            numero=1,
            periodo="2026-1",
            fecha=date(2026, 4, 15),
            titulo="Primer Parcial",
        )
        db_session.add(fa)
        await db_session.flush()
        assert fa.id is not None
        assert fa.tipo == "Parcial"
        assert fa.numero == 1
        assert fa.periodo == "2026-1"
        assert fa.fecha == date(2026, 4, 15)
        assert fa.titulo == "Primer Parcial"
        assert fa.deleted_at is None

    async def test_fecha_unique_constraint(self, db_session: AsyncSession):
        from app.models.fecha_academica import FechaAcademica

        tenant = await _create_tenant(db_session)
        materia = await _seed_materia(db_session, tenant.id)
        carrera = await _seed_carrera(db_session, tenant.id)
        cohorte = await _seed_cohorte(db_session, tenant.id, carrera.id)

        f1 = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Primero",
        )
        f2 = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 5, 1), titulo="Duplicado",
        )
        db_session.add_all([f1, f2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_fecha_tenant_isolation(self, db_session: AsyncSession):
        from app.models.fecha_academica import FechaAcademica

        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        m1 = await _seed_materia(db_session, t1.id, "M1")
        m2 = await _seed_materia(db_session, t2.id, "M2")
        c1 = await _seed_carrera(db_session, t1.id)
        c2 = await _seed_carrera(db_session, t2.id)
        ch1 = await _seed_cohorte(db_session, t1.id, c1.id)
        ch2 = await _seed_cohorte(db_session, t2.id, c2.id)

        f1 = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=t1.id,
            materia_id=m1.id, cohorte_id=ch1.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="T1",
        )
        f2 = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=t2.id,
            materia_id=m2.id, cohorte_id=ch2.id,
            tipo="TP", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 20), titulo="T2",
        )
        db_session.add_all([f1, f2])
        await db_session.flush()

        result = await db_session.execute(
            select(FechaAcademica).where(FechaAcademica.tenant_id == t1.id, FechaAcademica.deleted_at.is_(None))
        )
        t1_fechas = list(result.scalars().all())
        assert len(t1_fechas) == 1
        assert t1_fechas[0].titulo == "T1"


# ═══════════════════════════════════════════════════════
# 2. Tests de repositorios
# ═══════════════════════════════════════════════════════


class TestProgramaMateriaRepository:
    """ProgramaMateriaRepository CRUD and validations."""

    async def _seed(self, db, tenant_id):
        materia = await _seed_materia(db, tenant_id)
        carrera = await _seed_carrera(db, tenant_id)
        cohorte = await _seed_cohorte(db, tenant_id, carrera.id)
        return materia, carrera, cohorte

    async def test_create_programa(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        programa = await repo.create({
            "id": str(uuid.uuid4()),
            "materia_id": materia.id,
            "carrera_id": carrera.id,
            "cohorte_id": cohorte.id,
            "titulo": "Programa 2026",
            "referencia_archivo": "prog.pdf",
        })
        assert programa.id is not None
        assert programa.titulo == "Programa 2026"
        assert programa.tenant_id == tenant.id

    async def test_get_programa(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id,
            "titulo": "Get Test", "referencia_archivo": "g.pdf",
        })
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.titulo == "Get Test"

    async def test_list_programas(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        # Second carrera+cohorte for unique constraint compliance
        carrera2 = await _seed_carrera(db_session, tenant.id, "OTRA")
        cohorte2 = await _seed_cohorte(db_session, tenant.id, carrera2.id, "AGO-2026")
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id,
            "titulo": "P1", "referencia_archivo": "p1.pdf",
        })
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera2.id, "cohorte_id": cohorte2.id,
            "titulo": "P2", "referencia_archivo": "p2.pdf",
        })
        records = await repo.list()
        assert len(records) >= 2

    async def test_update_programa(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id,
            "titulo": "Original", "referencia_archivo": "o.pdf",
        })
        updated = await repo.update(created.id, {"titulo": "Updated"})
        assert updated is not None
        assert updated.titulo == "Updated"

    async def test_soft_delete_programa(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id,
            "titulo": "Delete Me", "referencia_archivo": "d.pdf",
        })
        deleted = await repo.soft_delete(created.id)
        assert deleted is True
        fetched = await repo.get(created.id)
        assert fetched is None

    async def test_exists_by_materia_carrera_cohorte_true(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id,
            "titulo": "Existe", "referencia_archivo": "e.pdf",
        })
        assert await repo.exists_by_materia_carrera_cohorte(materia.id, carrera.id, cohorte.id) is True

    async def test_exists_by_materia_carrera_cohorte_false(self, db_session: AsyncSession):
        from app.repositories.programa_repository import ProgramaMateriaRepository

        tenant = await _create_tenant(db_session)
        materia, carrera, cohorte = await self._seed(db_session, tenant.id)
        repo = ProgramaMateriaRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_materia_carrera_cohorte(materia.id, carrera.id, cohorte.id) is False


class TestFechaAcademicaRepository:
    """FechaAcademicaRepository CRUD and validations."""

    async def _seed(self, db, tenant_id):
        materia = await _seed_materia(db, tenant_id)
        carrera = await _seed_carrera(db, tenant_id)
        cohorte = await _seed_cohorte(db, tenant_id, carrera.id)
        return materia, carrera, cohorte

    async def test_create_fecha(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        fa = await repo.create({
            "id": str(uuid.uuid4()),
            "materia_id": materia.id,
            "cohorte_id": cohorte.id,
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": date(2026, 4, 15),
            "titulo": "Primer Parcial",
        })
        assert fa.id is not None
        assert fa.tipo == "Parcial"
        assert fa.fecha == date(2026, 4, 15)
        assert fa.tenant_id == tenant.id

    async def test_get_fecha(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "TP", "numero": 1,
            "periodo": "2026-1", "fecha": date(2026, 4, 20),
            "titulo": "Get Test",
        })
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.titulo == "Get Test"

    async def test_list_fechas(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1", "fecha": date(2026, 4, 15),
            "titulo": "P1",
        })
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": 2,
            "periodo": "2026-1", "fecha": date(2026, 6, 15),
            "titulo": "P2",
        })
        records = await repo.list()
        assert len(records) >= 2

    async def test_list_by_filters(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)

        for num in range(1, 4):
            await repo.create({
                "id": str(uuid.uuid4()), "materia_id": materia.id,
                "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": num,
                "periodo": "2026-1", "fecha": date(2026, 4, 10 + num),
                "titulo": f"Parcial {num}",
            })

        filtered = await repo.list_by_filters(tipo="Parcial", periodo="2026-1")
        assert len(filtered) >= 3

        filtered_tp = await repo.list_by_filters(tipo="TP")
        assert len(filtered_tp) == 0

    async def test_exists_by_unique_true(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1", "fecha": date(2026, 4, 15),
            "titulo": "Existe",
        })
        assert await repo.exists_by_unique(materia.id, cohorte.id, "Parcial", 1, "2026-1") is True

    async def test_exists_by_unique_false(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_unique(materia.id, cohorte.id, "Parcial", 99, "2026-1") is False

    async def test_update_fecha(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1", "fecha": date(2026, 4, 15),
            "titulo": "Original",
        })
        updated = await repo.update(created.id, {"titulo": "Updated"})
        assert updated is not None
        assert updated.titulo == "Updated"

    async def test_soft_delete_fecha(self, db_session: AsyncSession):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant = await _create_tenant(db_session)
        materia, _, cohorte = await self._seed(db_session, tenant.id)
        repo = FechaAcademicaRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({
            "id": str(uuid.uuid4()), "materia_id": materia.id,
            "cohorte_id": cohorte.id, "tipo": "Parcial", "numero": 1,
            "periodo": "2026-1", "fecha": date(2026, 4, 15),
            "titulo": "Delete Me",
        })
        deleted = await repo.soft_delete(created.id)
        assert deleted is True
        fetched = await repo.get(created.id)
        assert fetched is None


# ═══════════════════════════════════════════════════════
# 3. Tests de router
# ═══════════════════════════════════════════════════════


class TestProgramasRouter:
    """Router tests via HTTP for programas endpoints."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings

        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _build_app(self, db_session, settings, user):
        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.routers.programas import router as programas_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(programas_router)
        return app

    async def _create_admin_user(self, db, tenant_id):
        from tests.conftest import create_user

        u = await create_user(
            db, tenant_id,
            email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        await _seed_role_permiso(db, "admin", "estructura:gestionar")
        return u

    async def _seed_data(self, db, tenant_id):
        materia = await _seed_materia(db, tenant_id)
        carrera = await _seed_carrera(db, tenant_id)
        cohorte = await _seed_cohorte(db, tenant_id, carrera.id)
        return materia, carrera, cohorte

    async def test_create_programa_201(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/programas",
                json={
                    "materia_id": materia.id,
                    "carrera_id": carrera.id,
                    "cohorte_id": cohorte.id,
                    "titulo": "Programa 2026",
                    "referencia_archivo": "prog.pdf",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["titulo"] == "Programa 2026"
        assert data["materia_id"] == materia.id
        assert "id" in data

    async def test_list_programas_200(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="List Test", referencia_archivo="l.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/programas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        titulos = [d["titulo"] for d in data]
        assert "List Test" in titulos

    async def test_get_programa_by_id_200(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Get By ID", referencia_archivo="g.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/programas/{p.id}")
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Get By ID"

    async def test_get_programa_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/programas/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_create_programa_duplicado_409(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Original", referencia_archivo="o.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/programas",
                json={
                    "materia_id": materia.id,
                    "carrera_id": carrera.id,
                    "cohorte_id": cohorte.id,
                    "titulo": "Duplicado",
                    "referencia_archivo": "d.pdf",
                },
            )
        assert resp.status_code == 409
        assert "ya existe" in resp.json()["detail"].lower()

    async def test_update_programa_200(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Original", referencia_archivo="o.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/programas/{p.id}",
                json={"titulo": "Updated"},
            )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Updated"

    async def test_update_programa_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/programas/{uuid.uuid4()}",
                json={"titulo": "Nope"},
            )
        assert resp.status_code == 404

    async def test_delete_programa_204(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Delete Me", referencia_archivo="d.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/programas/{p.id}")
        assert resp.status_code == 204

    async def test_contenido_lms_200(self, db_session, test_settings):
        from app.models.programa_materia import ProgramaMateria

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, carrera, cohorte = await self._seed_data(db_session, tenant.id)
        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="LMS Test", referencia_archivo="lms.pdf",
        )
        db_session.add(p)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/programas/contenido-lms")
        assert resp.status_code == 200
        data = resp.json()
        assert "html" in data
        assert "Programas" in data["html"]
        assert "LMS Test" in data["html"]


class TestFechasAcademicasRouter:
    """Router tests via HTTP for fechas academicas endpoints."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings

        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _build_app(self, db_session, settings, user):
        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.routers.fechas_academicas import router as fechas_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(fechas_router)
        return app

    async def _create_admin_user(self, db, tenant_id):
        from tests.conftest import create_user

        u = await create_user(
            db, tenant_id,
            email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        await _seed_role_permiso(db, "admin", "estructura:gestionar")
        return u

    async def _seed_data(self, db, tenant_id):
        materia = await _seed_materia(db, tenant_id)
        carrera = await _seed_carrera(db, tenant_id)
        cohorte = await _seed_cohorte(db, tenant_id, carrera.id)
        return materia, carrera, cohorte

    async def test_create_fecha_201(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/fechas-academicas",
                json={
                    "materia_id": materia.id,
                    "cohorte_id": cohorte.id,
                    "tipo": "Parcial",
                    "numero": 1,
                    "periodo": "2026-1",
                    "fecha": "2026-04-15",
                    "titulo": "Primer Parcial",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "Parcial"
        assert data["numero"] == 1
        assert data["fecha"] == "2026-04-15"
        assert "id" in data

    async def test_list_fechas_200(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="List Test",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/fechas-academicas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        titulos = [d["titulo"] for d in data]
        assert "List Test" in titulos

    async def test_get_fecha_by_id_200(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="TP", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 20), titulo="Get By ID",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/fechas-academicas/{fa.id}")
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Get By ID"

    async def test_get_fecha_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/fechas-academicas/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_create_fecha_duplicada_409(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Original",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/fechas-academicas",
                json={
                    "materia_id": materia.id,
                    "cohorte_id": cohorte.id,
                    "tipo": "Parcial",
                    "numero": 1,
                    "periodo": "2026-1",
                    "fecha": "2026-05-01",
                    "titulo": "Duplicado",
                },
            )
        assert resp.status_code == 409
        assert "ya existe" in resp.json()["detail"].lower()

    async def test_update_fecha_200(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Original",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/fechas-academicas/{fa.id}",
                json={"titulo": "Updated"},
            )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Updated"

    async def test_update_fecha_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/fechas-academicas/{uuid.uuid4()}",
                json={"titulo": "Nope"},
            )
        assert resp.status_code == 404

    async def test_delete_fecha_204(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="Delete Me",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/fechas-academicas/{fa.id}")
        assert resp.status_code == 204

    async def test_contenido_lms_200(self, db_session, test_settings):
        from app.models.fecha_academica import FechaAcademica

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        materia, _, cohorte = await self._seed_data(db_session, tenant.id)
        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="LMS Test",
        )
        db_session.add(fa)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/fechas-academicas/contenido-lms")
        assert resp.status_code == 200
        data = resp.json()
        assert "html" in data
        assert "Calendario Evaluativo" in data["html"]
        assert "LMS Test" in data["html"]


# ═══════════════════════════════════════════════════════
# 4. Tests de permisos y aislamiento multi-tenant
# ═══════════════════════════════════════════════════════


class TestPermisosMultiTenant:
    """Verify 403 without permission and tenant isolation."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings

        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def test_usuario_sin_permiso_403(self, db_session, test_settings):
        """User without estructura:gestionar role gets 403."""
        from tests.conftest import create_user

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await create_user(
            db_session, tenant.id,
            email=f"alumno-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["alumno"],
        )
        await db_session.commit()

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.routers.programas import router as programas_router
        from app.routers.fechas_academicas import router as fechas_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(programas_router)
        app.include_router(fechas_router)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp_prog = await client.get("/api/programas")
            resp_fech = await client.get("/api/fechas-academicas")

        assert resp_prog.status_code == 403
        assert resp_fech.status_code == 403

    async def test_programas_tenant_isolated(self, db_session, test_settings):
        """Tenant A's programas are invisible to tenant B."""
        from tests.conftest import create_user
        from app.models.programa_materia import ProgramaMateria

        t_a = Tenant(id=str(uuid.uuid4()), slug=f"a-{uuid.uuid4().hex[:8]}", nombre="T A", estado="Activo")
        t_b = Tenant(id=str(uuid.uuid4()), slug=f"b-{uuid.uuid4().hex[:8]}", nombre="T B", estado="Activo")
        db_session.add_all([t_a, t_b])
        await db_session.flush()

        m_a = await _seed_materia(db_session, t_a.id, "MA")
        ca_a = await _seed_carrera(db_session, t_a.id)
        ch_a = await _seed_cohorte(db_session, t_a.id, ca_a.id)

        p = ProgramaMateria(
            id=str(uuid.uuid4()), tenant_id=t_a.id,
            materia_id=m_a.id, carrera_id=ca_a.id, cohorte_id=ch_a.id,
            titulo="TA_ONLY", referencia_archivo="ta.pdf",
        )
        db_session.add(p)

        user_b = await create_user(
            db_session, t_b.id,
            email=f"b-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "estructura:gestionar")
        await db_session.commit()

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.routers.programas import router as programas_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user_b

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(programas_router)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/programas")
        assert resp.status_code == 200
        data = resp.json()
        titulos = [d["titulo"] for d in data]
        assert "TA_ONLY" not in titulos

    async def test_fechas_tenant_isolated(self, db_session, test_settings):
        """Tenant A's fechas are invisible to tenant B."""
        from tests.conftest import create_user
        from app.models.fecha_academica import FechaAcademica

        t_a = Tenant(id=str(uuid.uuid4()), slug=f"a-{uuid.uuid4().hex[:8]}", nombre="T A", estado="Activo")
        t_b = Tenant(id=str(uuid.uuid4()), slug=f"b-{uuid.uuid4().hex[:8]}", nombre="T B", estado="Activo")
        db_session.add_all([t_a, t_b])
        await db_session.flush()

        m_a = await _seed_materia(db_session, t_a.id, "MA")
        ca_a = await _seed_carrera(db_session, t_a.id)
        ch_a = await _seed_cohorte(db_session, t_a.id, ca_a.id)

        fa = FechaAcademica(
            id=str(uuid.uuid4()), tenant_id=t_a.id,
            materia_id=m_a.id, cohorte_id=ch_a.id,
            tipo="Parcial", numero=1, periodo="2026-1",
            fecha=date(2026, 4, 15), titulo="TA_ONLY",
        )
        db_session.add(fa)

        user_b = await create_user(
            db_session, t_b.id,
            email=f"b-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "estructura:gestionar")
        await db_session.commit()

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.routers.fechas_academicas import router as fechas_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user_b

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(fechas_router)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/fechas-academicas")
        assert resp.status_code == 200
        data = resp.json()
        titulos = [d["titulo"] for d in data]
        assert "TA_ONLY" not in titulos
