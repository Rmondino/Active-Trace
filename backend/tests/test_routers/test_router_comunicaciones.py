"""Tests for comunicaciones router endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.crypto import CipherService
from app.models.comunicacion import Comunicacion
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import create_user


async def _create_tenant(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _seed_role_permiso(db_session, slug, codigo, alcance="global"):
    result = await db_session.execute(
        __import__("sqlalchemy").select(Rol).where(Rol.slug == slug)
    )
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db_session.add(role)
        await db_session.flush()

    result = await db_session.execute(
        __import__("sqlalchemy").select(Permiso).where(Permiso.codigo == codigo)
    )
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db_session.add(permiso)
        await db_session.flush()

    result = await db_session.execute(
        __import__("sqlalchemy").select(RolPermiso).where(
            RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id
        )
    )
    if result.scalar_one_or_none():
        return
    rp = RolPermiso(id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance)
    db_session.add(rp)
    await db_session.flush()


def _build_app(db_session, settings, user):
    from app.core.config import get_settings
    from app.core.current_user import get_current_user
    from app.core.database import get_db_session

    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db_override():
        yield db_session
    app.dependency_overrides[get_db_session] = _db_override

    from app.routers.comunicaciones import router as com_router
    app.include_router(com_router)
    return app


def _make_test_settings():
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestComunicacionesRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-COM-R", nombre="Test Com")
        db_session.add(materia)
        await db_session.flush()
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"com-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "comunicacion:enviar")
        await _seed_role_permiso(db_session, "coordinador", "comunicacion:aprobar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "user": user}

    async def test_403_without_permission(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"noperm-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/comunicaciones/preview",
                json={"materia_id": str(uuid.uuid4()), "asunto_template": "Hola", "cuerpo_template": "C", "alumnos": []},
            )
            assert response.status_code == 403

    async def test_preview_returns_previews_and_token(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/comunicaciones/preview",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto_template": "Hola {alumno_nombre}",
                    "cuerpo_template": "Querido {alumno_nombre} {alumno_apellidos}",
                    "alumnos": [
                        {"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"},
                    ],
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "previews" in data
            assert "preview_token" in data
            assert len(data["previews"]) == 1
            assert data["previews"][0]["asunto"] == "Hola Juan"

    async def test_enqueue_requires_preview(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/comunicaciones/enviar",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto": "Test",
                    "cuerpo": "Test",
                    "destinatarios": [{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
                },
            )
            assert response.status_code == 400
            assert "Preview requerido" in response.json()["detail"]

    async def test_enqueue_full_flow(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        settings_obj = _make_test_settings()
        cipher = CipherService(settings_obj)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            preview_resp = await client.post(
                "/api/comunicaciones/preview",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto_template": "Hola {alumno_nombre}",
                    "cuerpo_template": "Cuerpo {alumno_nombre}",
                    "alumnos": [{"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"}],
                },
            )
            assert preview_resp.status_code == 200
            token = preview_resp.json()["preview_token"]

            enqueue_resp = await client.post(
                "/api/comunicaciones/enviar",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto": "Hola Juan",
                    "cuerpo": "Cuerpo Juan",
                    "preview_token": token,
                    "destinatarios": [
                        {"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"},
                        {"email": "maria@test.com", "nombre": "María", "apellidos": "Gómez"},
                    ],
                },
            )
            assert enqueue_resp.status_code == 200
            data = enqueue_resp.json()
            assert "lote_id" in data
            assert data["total"] == 2

    async def test_enqueue_with_expired_token_returns_400(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        from app.services.comunicacion_service import _preview_store
        _preview_store.clear()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/comunicaciones/enviar",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto": "Test",
                    "cuerpo": "Test",
                    "preview_token": str(uuid.uuid4()),
                    "destinatarios": [{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
                },
            )
            assert response.status_code == 400
            assert "no encontrado" in response.json()["detail"].lower()

    async def test_enqueue_with_used_token_returns_400(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        from app.services.comunicacion_service import _preview_store, _store_preview
        _preview_store.clear()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = _store_preview({
                "materia_id": seed["materia_id"],
                "asunto_template": "Test",
                "cuerpo_template": "Test",
                "alumnos": [{"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"}],
                "tenant_id": seed["tenant_id"],
            })

            resp1 = await client.post(
                "/api/comunicaciones/enviar",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto": "Test",
                    "cuerpo": "Test",
                    "preview_token": token,
                    "destinatarios": [{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
                },
            )
            assert resp1.status_code == 200

            resp2 = await client.post(
                "/api/comunicaciones/enviar",
                json={
                    "materia_id": seed["materia_id"],
                    "asunto": "Test",
                    "cuerpo": "Test",
                    "preview_token": token,
                    "destinatarios": [{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
                },
            )
            assert resp2.status_code == 400
            assert "ya utilizado" in resp2.json()["detail"]

    async def test_tracking(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        lote = str(uuid.uuid4())
        coms = [
            Comunicacion(
                id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
                enviado_por=seed["user"].id, materia_id=seed["materia_id"],
                destinatario="enc", asunto="A", cuerpo="C", lote_id=lote,
            )
            for _ in range(2)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/comunicaciones",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            for item in data:
                assert "estado" in item
                assert "asunto" in item

    async def test_pendientes_aprobacion(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        lote = str(uuid.uuid4())
        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            enviado_por=seed["user"].id, materia_id=seed["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C",
            lote_id=lote, estado="Pendiente",
        )
        db_session.add(com)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/comunicaciones/pendientes-aprobacion")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert data[0]["lote_id"] == lote

    async def test_aprobar_lote(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        lote = str(uuid.uuid4())
        coms = [
            Comunicacion(
                id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
                enviado_por=seed["user"].id, materia_id=seed["materia_id"],
                destinatario="enc", asunto="A", cuerpo="C", lote_id=lote,
            )
            for _ in range(3)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/comunicaciones/aprobar/lote/{lote}")
            assert response.status_code == 200
            data = response.json()
            assert data["aprobados"] == 3

    async def test_aprobar_individual(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            enviado_por=seed["user"].id, materia_id=seed["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C",
            lote_id=str(uuid.uuid4()), estado="Pendiente",
        )
        db_session.add(com)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/comunicaciones/aprobar/{com.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["estado"] == "Pendiente"

    async def test_rechazar(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            enviado_por=seed["user"].id, materia_id=seed["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C",
            lote_id=str(uuid.uuid4()), estado="Pendiente",
        )
        db_session.add(com)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/comunicaciones/rechazar/{com.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["estado"] == "Cancelado"

    async def test_rechazar_enviado_returns_400(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            enviado_por=seed["user"].id, materia_id=seed["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C",
            lote_id=str(uuid.uuid4()), estado="Enviado",
        )
        db_session.add(com)
        await db_session.flush()

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/comunicaciones/rechazar/{com.id}")
            assert response.status_code == 400
            assert "Estado terminal" in response.json()["detail"]
