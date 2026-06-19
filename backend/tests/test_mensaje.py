"""Tests for C-20 mensajería interna (inbox)."""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from tests.conftest import create_user


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


def _build_app(db_session, settings, user):
    from fastapi import FastAPI
    from app.core.config import get_settings
    from app.core.current_user import get_current_user
    from app.core.database import get_db_session

    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db_override():
        yield db_session
    app.dependency_overrides[get_db_session] = _db_override

    from app.routers.inbox import router as inbox_router
    app.include_router(inbox_router)
    return app


class TestInboxRouter:
    """Mensajería interna: enviar, listar, leer, responder."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def test_enviar_y_listar_recibidos(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        remitente = await create_user(
            db_session, tenant.id,
            email=f"remitente-{uuid.uuid4().hex[:8]}@test.com",
            nombre="Remitente", apellidos="Test",
        )
        destinatario = await create_user(
            db_session, tenant.id,
            email=f"dest-{uuid.uuid4().hex[:8]}@test.com",
            nombre="Destinatario", apellidos="Test",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, remitente)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/inbox", json={
                "destinatario_id": destinatario.id,
                "asunto": "Hola",
                "cuerpo": "Mensaje de prueba",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["asunto"] == "Hola"
        assert data["remitente_id"] == remitente.id
        assert data["destinatario_id"] == destinatario.id

        # Listar recibidos como destinatario
        app2 = _build_app(db_session, test_settings, destinatario)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            resp = await client.get("/api/inbox")
        assert resp.status_code == 200
        mensajes = resp.json()
        assert len(mensajes) == 1
        assert mensajes[0]["id"] == data["id"]

    async def test_marcar_leido_al_ver_detalle(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        remitente = await create_user(
            db_session, tenant.id,
            email=f"rem2-{uuid.uuid4().hex[:8]}@test.com",
        )
        destinatario = await create_user(
            db_session, tenant.id,
            email=f"dest2-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        # Enviar mensaje
        app = _build_app(db_session, test_settings, remitente)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/inbox", json={
                "destinatario_id": destinatario.id,
                "asunto": "Leer esto",
                "cuerpo": "Cuerpo del mensaje",
            })
        mensaje_id = resp.json()["id"]

        # Destinatario ve detalle → marca leído
        app2 = _build_app(db_session, test_settings, destinatario)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            resp = await client.get(f"/api/inbox/{mensaje_id}")
        assert resp.status_code == 200
        assert resp.json()["leido"] is True
        assert resp.json()["leido_at"] is not None

    async def test_responder_mensaje(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_a = await create_user(
            db_session, tenant.id,
            email=f"a-{uuid.uuid4().hex[:8]}@test.com",
        )
        user_b = await create_user(
            db_session, tenant.id,
            email=f"b-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        # A envía a B
        app = _build_app(db_session, test_settings, user_a)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/inbox", json={
                "destinatario_id": user_b.id,
                "asunto": "Pregunta",
                "cuerpo": "¿Vamos?",
            })
        padre_id = resp.json()["id"]

        # B responde
        app2 = _build_app(db_session, test_settings, user_b)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            resp = await client.post(f"/api/inbox/{padre_id}/responder", json={
                "cuerpo": "Dale vamos",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["asunto"] == "Re: Pregunta"
        assert data["mensaje_padre_id"] == padre_id
        assert data["remitente_id"] == user_b.id
        assert data["destinatario_id"] == user_a.id

        # A recibe la respuesta
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/inbox")
        assert resp.status_code == 200
        asuntos = [m["asunto"] for m in resp.json()]
        assert "Re: Pregunta" in asuntos

    async def test_contar_no_leidos(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        remitente = await create_user(
            db_session, tenant.id,
            email=f"rem3-{uuid.uuid4().hex[:8]}@test.com",
        )
        destinatario = await create_user(
            db_session, tenant.id,
            email=f"dest3-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, remitente)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/inbox", json={
                "destinatario_id": destinatario.id,
                "asunto": "Aviso",
                "cuerpo": "No leído",
            })

        app2 = _build_app(db_session, test_settings, destinatario)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            resp = await client.get("/api/inbox/no-leidos")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    async def test_listar_enviados(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        remitente = await create_user(
            db_session, tenant.id,
            email=f"rem4-{uuid.uuid4().hex[:8]}@test.com",
        )
        destinatario = await create_user(
            db_session, tenant.id,
            email=f"dest4-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, remitente)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/inbox", json={
                "destinatario_id": destinatario.id,
                "asunto": "Enviado",
                "cuerpo": "Test",
            })

            resp = await client.get("/api/inbox/enviados")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["asunto"] == "Enviado"

    async def test_enviar_403_por_extra_fields(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"extra-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/inbox", json={
                "destinatario_id": user.id,
                "asunto": "Test",
                "cuerpo": "Cuerpo",
                "extra_field": "no-permitido",
            })
        assert resp.status_code == 422

    async def test_responder_404_si_no_existe(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"resp404-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/inbox/{uuid.uuid4()}/responder", json={
                "cuerpo": "Nadie",
            })
        assert resp.status_code == 404

    async def test_detalle_404_si_no_existe(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"det404-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/inbox/{uuid.uuid4()}")
        assert resp.status_code == 404
