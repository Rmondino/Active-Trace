"""Tests for C-06 Estructura Academica (modelos, repositorios, router, multi-tenant).
"""

import uuid

import pytest
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


# ═══════════════════════════════════════════════════════
# 5.1 Tests de modelos
# ═══════════════════════════════════════════════════════


class TestCarreraModel:
    """Model creation and constraints for Carrera."""

    async def test_create_carrera(self, db_session: AsyncSession):
        from app.models.carrera import Carrera

        tenant = await _create_tenant(db_session)
        carrera = Carrera(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            codigo="TUPAD",
            nombre="Tecnicatura Universitaria en Programación y Administración de Datos",
            estado="Activa",
        )
        db_session.add(carrera)
        await db_session.flush()
        assert carrera.id is not None
        assert carrera.codigo == "TUPAD"
        assert carrera.nombre == "Tecnicatura Universitaria en Programación y Administración de Datos"
        assert carrera.estado == "Activa"
        assert carrera.deleted_at is None
        assert carrera.tenant_id == tenant.id

    async def test_carrera_default_estado(self, db_session: AsyncSession):
        from app.models.carrera import Carrera

        tenant = await _create_tenant(db_session)
        carrera = Carrera(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            codigo="TUPAD2",
            nombre="Otra Tecnicatura",
        )
        db_session.add(carrera)
        await db_session.flush()
        assert carrera.estado == "Activa"

    async def test_carrera_unique_codigo_per_tenant(self, db_session: AsyncSession):
        import sqlalchemy.exc
        from app.models.carrera import Carrera

        tenant = await _create_tenant(db_session)
        c1 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UNICO", nombre="Una")
        c2 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UNICO", nombre="Dos")
        db_session.add_all([c1, c2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_carrera_same_codigo_different_tenant_allowed(self, db_session: AsyncSession):
        from app.models.carrera import Carrera

        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        c1 = Carrera(id=str(uuid.uuid4()), tenant_id=t1.id, codigo="MISMO", nombre="Carrera T1")
        c2 = Carrera(id=str(uuid.uuid4()), tenant_id=t2.id, codigo="MISMO", nombre="Carrera T2")
        db_session.add_all([c1, c2])
        await db_session.flush()
        assert c1.id != c2.id
        assert c1.codigo == c2.codigo
        assert c1.tenant_id != c2.tenant_id


class TestCohorteModel:
    """Model creation and constraints for Cohorte."""

    async def test_create_cohorte(self, db_session: AsyncSession):
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte

        tenant = await _create_tenant(db_session)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="TUPAD", nombre="Tecnicatura")
        db_session.add(carrera)
        await db_session.flush()

        cohorte = Cohorte(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            carrera_id=carrera.id,
            nombre="MAR-2026",
            anio=2026,
            vig_desde="2026-03-01",
            estado="Activa",
        )
        db_session.add(cohorte)
        await db_session.flush()
        assert cohorte.id is not None
        assert cohorte.nombre == "MAR-2026"
        assert cohorte.anio == 2026
        assert cohorte.carrera_id == carrera.id
        assert cohorte.vig_hasta is None

    async def test_cohorte_unique_nombre_per_carrera(self, db_session: AsyncSession):
        import sqlalchemy.exc
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte

        tenant = await _create_tenant(db_session)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="TUPAD", nombre="Tecnicatura")
        db_session.add(carrera)
        await db_session.flush()

        ch1 = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="UNICA", anio=2026)
        ch2 = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="UNICA", anio=2027)
        db_session.add_all([ch1, ch2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()


class TestMateriaModel:
    """Model creation and constraints for Materia."""

    async def test_create_materia(self, db_session: AsyncSession):
        from app.models.materia import Materia

        tenant = await _create_tenant(db_session)
        materia = Materia(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            codigo="PROG_I",
            nombre="Programación I",
            estado="Activa",
        )
        db_session.add(materia)
        await db_session.flush()
        assert materia.id is not None
        assert materia.codigo == "PROG_I"
        assert materia.nombre == "Programación I"
        assert materia.estado == "Activa"
        assert materia.deleted_at is None

    async def test_materia_unique_codigo_per_tenant(self, db_session: AsyncSession):
        import sqlalchemy.exc
        from app.models.materia import Materia

        tenant = await _create_tenant(db_session)
        m1 = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UNICO", nombre="Materia 1")
        m2 = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UNICO", nombre="Materia 2")
        db_session.add_all([m1, m2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()


# ═══════════════════════════════════════════════════════
# 5.2 Tests de repositorios
# ═══════════════════════════════════════════════════════


class TestCarreraRepository:
    """CarreraRepository CRUD and validations."""

    async def test_create_carrera(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        carrera = await repo.create({
            "id": str(uuid.uuid4()),
            "codigo": "TUPAD",
            "nombre": "Tecnicatura",
        })
        assert carrera.id is not None
        assert carrera.codigo == "TUPAD"
        assert carrera.tenant_id == tenant.id

    async def test_get_carrera(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({"id": str(uuid.uuid4()), "codigo": "GET_TEST", "nombre": "Get Test"})
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.nombre == "Get Test"

    async def test_list_carreras(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({"id": str(uuid.uuid4()), "codigo": "C1", "nombre": "C1"})
        await repo.create({"id": str(uuid.uuid4()), "codigo": "C2", "nombre": "C2"})
        records = await repo.list()
        assert len(records) >= 2

    async def test_update_carrera(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({"id": str(uuid.uuid4()), "codigo": "UPD", "nombre": "Original"})
        updated = await repo.update(created.id, {"nombre": "Updated"})
        assert updated is not None
        assert updated.nombre == "Updated"

    async def test_soft_delete_carrera(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({"id": str(uuid.uuid4()), "codigo": "SD", "nombre": "Soft Delete"})
        deleted = await repo.soft_delete(created.id)
        assert deleted is True
        fetched = await repo.get(created.id)
        assert fetched is None

    async def test_restore_carrera(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        created = await repo.create({"id": str(uuid.uuid4()), "codigo": "REST", "nombre": "Restore"})
        await repo.soft_delete(created.id)
        restored = await repo.restore(created.id)
        assert restored is True
        fetched = await repo.get(created.id)
        assert fetched is not None

    async def test_exists_by_codigo_true(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({"id": str(uuid.uuid4()), "codigo": "EXISTE", "nombre": "Existe"})
        assert await repo.exists_by_codigo("EXISTE") is True

    async def test_exists_by_codigo_false(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        tenant = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_codigo("NO_EXISTE") is False

    async def test_exists_by_codigo_other_tenant_not_found(self, db_session: AsyncSession):
        from app.repositories.carrera_repository import CarreraRepository

        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        repo = CarreraRepository(session=db_session, tenant_id=t1.id)
        await repo.create({"id": str(uuid.uuid4()), "codigo": "T1_ONLY", "nombre": "T1"})
        repo2 = CarreraRepository(session=db_session, tenant_id=t2.id)
        assert await repo2.exists_by_codigo("T1_ONLY") is False


class TestCohorteRepository:
    """CohorteRepository CRUD and validations."""

    async def _seed_carrera(self, db, tenant_id, codigo="CAR", estado="Activa"):
        from app.models.carrera import Carrera
        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant_id, codigo=codigo, nombre="Carrera Test", estado=estado)
        db.add(c)
        await db.flush()
        return c

    async def test_create_cohorte(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id)
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        cohorte = await repo.create({
            "id": str(uuid.uuid4()),
            "carrera_id": carrera.id,
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        })
        assert cohorte.id is not None
        assert cohorte.nombre == "MAR-2026"
        assert cohorte.carrera_id == carrera.id

    async def test_exists_by_nombre_y_carrera_true(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id)
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "id": str(uuid.uuid4()), "carrera_id": carrera.id,
            "nombre": "UNICO", "anio": 2026, "vig_desde": "2026-01-01",
        })
        assert await repo.exists_by_nombre_y_carrera("UNICO", carrera.id) is True

    async def test_exists_by_nombre_y_carrera_false(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id)
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_nombre_y_carrera("NO_EXISTE", carrera.id) is False

    async def test_create_cohorte_abierta_en_carrera_inactiva_rejected(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id, estado="Inactiva")
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        with pytest.raises(ValueError, match="No se pueden crear cohortes abiertas para una carrera inactiva"):
            await repo.create({
                "id": str(uuid.uuid4()), "carrera_id": carrera.id,
                "nombre": "ABIERTA", "anio": 2026, "vig_desde": "2026-01-01",
            })

    async def test_create_cohorte_cerrada_en_carrera_inactiva_allowed(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id, estado="Inactiva")
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        cohorte = await repo.create({
            "id": str(uuid.uuid4()), "carrera_id": carrera.id,
            "nombre": "CERRADA", "anio": 2026, "vig_desde": "2026-01-01",
            "vig_hasta": "2026-12-31",
        })
        assert cohorte is not None
        assert cohorte.vig_hasta == "2026-12-31"

    async def test_create_cohorte_abierta_en_carrera_activa_allowed(self, db_session: AsyncSession):
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = await _create_tenant(db_session)
        carrera = await self._seed_carrera(db_session, tenant.id, estado="Activa")
        repo = CohorteRepository(session=db_session, tenant_id=tenant.id)
        cohorte = await repo.create({
            "id": str(uuid.uuid4()), "carrera_id": carrera.id,
            "nombre": "ABIERTA", "anio": 2026, "vig_desde": "2026-01-01",
        })
        assert cohorte is not None
        assert cohorte.vig_hasta is None


class TestMateriaRepository:
    """MateriaRepository CRUD and validations."""

    async def test_create_materia(self, db_session: AsyncSession):
        from app.repositories.materia_repository import MateriaRepository

        tenant = await _create_tenant(db_session)
        repo = MateriaRepository(session=db_session, tenant_id=tenant.id)
        materia = await repo.create({
            "id": str(uuid.uuid4()), "codigo": "PROG_I", "nombre": "Programación I",
        })
        assert materia.id is not None
        assert materia.codigo == "PROG_I"

    async def test_list_materias(self, db_session: AsyncSession):
        from app.repositories.materia_repository import MateriaRepository

        tenant = await _create_tenant(db_session)
        repo = MateriaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({"id": str(uuid.uuid4()), "codigo": "M1", "nombre": "Materia 1"})
        await repo.create({"id": str(uuid.uuid4()), "codigo": "M2", "nombre": "Materia 2"})
        records = await repo.list()
        assert len(records) >= 2

    async def test_exists_by_codigo_true(self, db_session: AsyncSession):
        from app.repositories.materia_repository import MateriaRepository

        tenant = await _create_tenant(db_session)
        repo = MateriaRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({"id": str(uuid.uuid4()), "codigo": "M_EXISTE", "nombre": "M Existe"})
        assert await repo.exists_by_codigo("M_EXISTE") is True

    async def test_exists_by_codigo_false(self, db_session: AsyncSession):
        from app.repositories.materia_repository import MateriaRepository

        tenant = await _create_tenant(db_session)
        repo = MateriaRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_codigo("M_NO_EXISTE") is False


# ═══════════════════════════════════════════════════════
# 5.3 Tests de router
# ═══════════════════════════════════════════════════════


class TestEstructuraRouter:
    """Router tests via HTTP with dependency overrides."""

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
        from app.routers.admin.estructura import router as estructura_router

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override
        app.include_router(estructura_router)
        return app

    async def _create_admin_user(self, db, tenant_id):
        from tests.conftest import create_user

        u = await create_user(
            db, tenant_id,
            email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        # Seed the required permission for the admin role
        await _seed_role_permiso(db, "admin", "estructura:gestionar")
        return u

    @pytest.fixture
    def _cors_override(self, monkeypatch):
        """Avoid CORS middleware in test app."""
        pass

    # ── CRUD Carreras ──

    async def test_create_carrera_201(self, db_session, test_settings):
        from app.models.tenant import Tenant

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/carreras",
                json={"codigo": "TUPAD", "nombre": "Tecnicatura"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "TUPAD"
        assert data["estado"] == "Activa"
        assert "id" in data

    async def test_list_carreras_200(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="LC", nombre="Licenciatura")
        db_session.add(c)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/carreras")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        codes = [d["codigo"] for d in data]
        assert "LC" in codes

    async def test_get_carrera_by_id_200(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="IDTEST", nombre="ID Test")
        db_session.add(c)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/carreras/{c.id}")
        assert resp.status_code == 200
        assert resp.json()["codigo"] == "IDTEST"

    async def test_get_carrera_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/carreras/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_create_carrera_duplicada_409(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="DUP", nombre="Original")
        db_session.add(c)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/carreras",
                json={"codigo": "DUP", "nombre": "Duplicada"},
            )
        assert resp.status_code == 409
        assert "ya existe" in resp.json()["detail"].lower()

    async def test_update_carrera_200(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UPD", nombre="Original")
        db_session.add(c)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/admin/carreras/{c.id}",
                json={"nombre": "Updated", "estado": "Inactiva"},
            )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Updated"
        assert resp.json()["estado"] == "Inactiva"

    async def test_update_carrera_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/admin/carreras/{uuid.uuid4()}",
                json={"nombre": "Nope"},
            )
        assert resp.status_code == 404

    async def test_delete_carrera_204(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="DEL", nombre="Delete Me")
        db_session.add(c)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/admin/carreras/{c.id}")
        assert resp.status_code == 204

    # ── Regla carrera-inactiva ──

    async def test_cohorte_abierta_en_carrera_inactiva_400(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="INACT", nombre="Inactiva", estado="Inactiva")
        db_session.add(carrera)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/cohortes",
                json={
                    "carrera_id": carrera.id,
                    "nombre": "ABIERTA",
                    "anio": 2026,
                    "vig_desde": "2026-03-01",
                },
            )
        assert resp.status_code == 400
        assert "carrera inactiva" in resp.json()["detail"].lower()

    async def test_cohorte_cerrada_en_carrera_inactiva_201(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="INACT2", nombre="Inactiva", estado="Inactiva")
        db_session.add(carrera)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/cohortes",
                json={
                    "carrera_id": carrera.id,
                    "nombre": "CERRADA",
                    "anio": 2026,
                    "vig_desde": "2026-03-01",
                    "vig_hasta": "2026-12-31",
                },
            )
        assert resp.status_code == 201

    # ── Cohorte CRUD ──

    async def test_create_cohorte_201(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CR", nombre="Carrera")
        db_session.add(carrera)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/cohortes",
                json={
                    "carrera_id": carrera.id,
                    "nombre": "MAR-2026",
                    "anio": 2026,
                    "vig_desde": "2026-03-01",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "MAR-2026"
        assert data["carrera_id"] == carrera.id

    # ── Materia CRUD ──

    async def test_create_materia_201(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/materias",
                json={"codigo": "PROG_I", "nombre": "Programación I"},
            )
        assert resp.status_code == 201
        assert resp.json()["codigo"] == "PROG_I"

    async def test_list_materias_200(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/materias")
        assert resp.status_code == 200

    # ── Cohorte additional endpoints ──

    async def test_list_cohortes_filter_by_carrera(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        c1 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="C1", nombre="Carrera 1")
        c2 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="C2", nombre="Carrera 2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/cohortes?carrera_id={c1.id}")
        assert resp.status_code == 200

    async def test_get_cohorte_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/cohortes/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_update_cohorte_200(self, db_session, test_settings):
        from app.models.carrera import Carrera

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UPDC", nombre="Carrera Upd")
        db_session.add(carrera)
        await db_session.flush()

        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="ORG", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/admin/cohortes/{cohorte.id}",
                json={"nombre": "UPDATED"},
            )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "UPDATED"

    async def test_delete_cohorte_204(self, db_session, test_settings):
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="DELC", nombre="Carrera Del")
        db_session.add(carrera)
        await db_session.flush()

        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="DEL", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/admin/cohortes/{cohorte.id}")
        assert resp.status_code == 204

    # ── Materia additional endpoints ──

    async def test_get_materia_by_id_200(self, db_session, test_settings):
        from app.models.materia import Materia

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        m = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="GETM", nombre="Get Materia")
        db_session.add(m)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/materias/{m.id}")
        assert resp.status_code == 200
        assert resp.json()["codigo"] == "GETM"

    async def test_get_materia_404(self, db_session, test_settings):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/materias/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_update_materia_200(self, db_session, test_settings):
        from app.models.materia import Materia

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        m = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="UPDM", nombre="Original")
        db_session.add(m)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/api/admin/materias/{m.id}",
                json={"nombre": "Updated"},
            )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Updated"

    async def test_delete_materia_204(self, db_session, test_settings):
        from app.models.materia import Materia

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        m = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="DELM", nombre="Delete Me")
        db_session.add(m)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/admin/materias/{m.id}")
        assert resp.status_code == 204

    async def test_create_materia_duplicada_409(self, db_session, test_settings):
        from app.models.materia import Materia

        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()

        m = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="DUP", nombre="Original")
        db_session.add(m)
        await db_session.flush()

        user = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/materias",
                json={"codigo": "DUP", "nombre": "Duplicada"},
            )
        assert resp.status_code == 409

    # ── 403 sin permiso ──

    async def test_usuario_sin_permiso_403(self, db_session, test_settings):
        """User without admin role (no estructura:gestionar) gets 403."""
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

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/carreras")
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════
# 5.4 Tests de aislamiento multi-tenant
# ═══════════════════════════════════════════════════════


class TestMultiTenantIsolation:
    """Verify tenant A's data is invisible to tenant B."""

    async def test_carreras_isolated(self, db_session, test_settings):
        from app.models.carrera import Carrera
        from tests.conftest import create_user

        t_a = Tenant(id=str(uuid.uuid4()), slug=f"a-{uuid.uuid4().hex[:8]}", nombre="T A", estado="Activo")
        t_b = Tenant(id=str(uuid.uuid4()), slug=f"b-{uuid.uuid4().hex[:8]}", nombre="T B", estado="Activo")
        db_session.add_all([t_a, t_b])
        await db_session.flush()

        c = Carrera(id=str(uuid.uuid4()), tenant_id=t_a.id, codigo="TA_ONLY", nombre="Solo A")
        db_session.add(c)
        await db_session.flush()

        user_b = await create_user(
            db_session, t_b.id,
            email=f"b-{uuid.uuid4().hex[:8]}@test.com",
            password="Pass1234!",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "estructura:gestionar")
        await db_session.commit()

        app = _build_app_isolated(db_session, test_settings, user_b)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/carreras")
        assert resp.status_code == 200
        data = resp.json()
        codes = [d["codigo"] for d in data]
        assert "TA_ONLY" not in codes


def _build_app_isolated(db_session, settings, user):
    """Helper: build a minimal FastAPI app with the estructura router."""
    from fastapi import FastAPI
    from app.core.config import get_settings
    from app.core.current_user import get_current_user
    from app.core.database import get_db_session
    from app.routers.admin.estructura import router as estructura_router

    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db_override():
        yield db_session

    app.dependency_overrides[get_db_session] = _db_override
    app.include_router(estructura_router)
    return app
