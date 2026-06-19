"""Tests for impersonación endpoints."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.tenant import Tenant
from tests.conftest import create_user


async def _seed_role_permiso(db, slug, codigo, alcance="global"):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso
    from sqlalchemy import select

    result = await db.execute(select(Rol).where(Rol.slug == slug))
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db.add(role)
        await db.flush()

    result = await db.execute(select(Permiso).where(Permiso.codigo == codigo))
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db.add(permiso)
        await db.flush()

    result = await db.execute(
        select(RolPermiso).where(RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id)
    )
    if result.scalar_one_or_none():
        return
    rp = RolPermiso(id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance)
    db.add(rp)
    await db.flush()


async def _create_tenant(db) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


async def _get_token_for_user(user, settings):
    from app.core.jwt import create_access_token
    return create_access_token(user, settings)


async def _get_impersonation_token(target_user, settings, actor_original_id):
    from app.core.jwt import create_access_token
    return create_access_token(
        user=target_user, settings=settings,
        impersonando=True, actor_original_id=actor_original_id,
    )


class TestImpersonacion:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed_impersonable(self, db_session, test_settings):
        """Seed tenant + admin user with impersonacion:usar."""
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "impersonacion:usar")
        token = await _get_token_for_user(user, test_settings)
        return {"tenant": tenant, "user": user, "token": token}

    async def _seed_target_user(self, db_session, tenant_id):
        target = await create_user(
            db_session, tenant_id,
            email=f"target-{uuid.uuid4().hex[:8]}@test.com",
        )
        return target

    def _build_app(self, db_session, test_settings):
        """Build app with the impersonación router and all deps overridden."""
        from app.core.config import get_settings
        from app.core.database import get_db_session

        from app.main import create_app
        app = create_app(settings=test_settings)
        app.dependency_overrides[get_settings] = lambda: test_settings

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        return app

    async def test_impersonar_returns_jwt_with_impersonando_flag(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        target = await self._seed_target_user(db_session, seed["tenant"].id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": target.id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["impersonando"] is True

        from app.core.jwt import decode_token_unsafe
        claims = decode_token_unsafe(data["access_token"])
        assert claims.get("impersonando") is True
        assert claims.get("actor_original_id") == seed["user"].id
        assert claims.get("sub") == target.id

    async def test_impersonar_sin_permiso_returns_403(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(
            db_session, tenant.id,
            email=f"noperm-{uuid.uuid4().hex[:8]}@test.com",
        )
        token = await _get_token_for_user(user_no_perm, test_settings)
        target = await self._seed_target_user(db_session, tenant.id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": target.id},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 403

    async def test_impersonar_usuario_inexistente_returns_404(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        fake_id = str(uuid.uuid4())

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": fake_id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp.status_code == 404

    async def test_impersonar_otro_tenant_returns_404(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        other_tenant = await _create_tenant(db_session)
        other_user = await self._seed_target_user(db_session, other_tenant.id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": other_user.id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp.status_code == 404

    async def test_dejar_impersonar_restaura_jwt(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        target = await self._seed_target_user(db_session, seed["tenant"].id)

        # First impersonate
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_imp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": target.id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp_imp.status_code == 200
        impersonated_token = resp_imp.json()["access_token"]

        # Then dejate impersonar
        transport2 = ASGITransport(app=app)
        async with AsyncClient(transport=transport2, base_url="http://test") as client:
            resp_dejar = await client.post(
                "/api/auth/dejar-impersonar",
                headers={"Authorization": f"Bearer {impersonated_token}"},
            )
        assert resp_dejar.status_code == 200
        data = resp_dejar.json()
        assert "access_token" in data
        assert data["impersonando"] is False

        from app.core.jwt import decode_token_unsafe
        claims = decode_token_unsafe(data["access_token"])
        assert claims.get("impersonando") is False
        assert claims.get("sub") == seed["user"].id

    async def test_impersonar_crea_audit_entry(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        target = await self._seed_target_user(db_session, seed["tenant"].id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": target.id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp.status_code == 200

        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        logs = await repo.get_all(seed["tenant"].id, filtros={"accion": "IMPERSONACION_INICIAR"})
        assert len(logs) == 1
        assert logs[0].actor_id == seed["user"].id
        assert logs[0].impersonado_id == target.id
        assert logs[0].accion == "IMPERSONACION_INICIAR"

    async def test_dejar_impersonar_crea_audit_entry(self, db_session, test_settings):
        app = self._build_app(db_session, test_settings)
        seed = await self._seed_impersonable(db_session, test_settings)
        target = await self._seed_target_user(db_session, seed["tenant"].id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_imp = await client.post(
                "/api/auth/impersonar",
                json={"usuario_id": target.id},
                headers={"Authorization": f"Bearer {seed['token']}"},
            )
        assert resp_imp.status_code == 200
        impersonated_token = resp_imp.json()["access_token"]

        transport2 = ASGITransport(app=app)
        async with AsyncClient(transport=transport2, base_url="http://test") as client:
            resp_dejar = await client.post(
                "/api/auth/dejar-impersonar",
                headers={"Authorization": f"Bearer {impersonated_token}"},
            )
        assert resp_dejar.status_code == 200

        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository(db_session)
        logs = await repo.get_all(seed["tenant"].id, filtros={"accion": "IMPERSONACION_FINALIZAR"})
        assert len(logs) == 1
        assert logs[0].actor_id == seed["user"].id
        assert logs[0].impersonado_id == target.id
        assert logs[0].accion == "IMPERSONACION_FINALIZAR"
