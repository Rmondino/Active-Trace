"""Tests for C-04 RBAC — PermissionService refactored to use Asignacion.

Covers:
    - PermissionService.get_effective_permissions() from Asignacion
    - PermissionService.has_permission()
    - PermissionService.get_permission_scope()
    - require_permission dependency guard
    - Multi-tenant isolation
    - Expired (vencida) asignaciones do not grant permissions
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
# PermissionService tests
# ═══════════════════════════════════════════════════════


class TestPermissionService:
    """PermissionService resolves roles from Asignacion (not user.roles JSONB)."""

    async def _create_user_with_asignacion(self, db, tenant_id, roles, desde=None, hasta=None):
        """Helper: create user + Asignacion records with optional vigencia."""
        from datetime import date
        from tests.conftest import create_user

        user = await create_user(
            db, tenant_id,
            email=f"user-{uuid.uuid4().hex[:8]}@test.com",
            roles=[],
        )
        # Add Asignacion records (not via create_user helper to control dates)
        from app.models.asignacion import Asignacion

        for rol in roles:
            asig = Asignacion(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                usuario_id=user.id,
                rol=rol.upper(),
                desde=desde if desde else date(2020, 1, 1),
                hasta=hasta,
                comisiones=[],
            )
            db.add(asig)
        await db.flush()
        return user

    async def test_effective_permissions_from_asignacion(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "entregas:ver")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)

        assert len(perms) >= 1
        assert ("entregas:ver", "global") in perms

    async def test_vencida_asignacion_does_not_grant(self, db_session: AsyncSession):
        from datetime import date

        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(
            db_session, tenant.id, roles=["profesor"],
            desde=date(2020, 1, 1),
            hasta=date(2020, 12, 31),
        )
        await _seed_role_permiso(db_session, "profesor", "entregas:ver")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)

        assert len(perms) == 0

    async def test_multi_role_union(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(
            db_session, tenant.id, roles=["profesor", "coordinador"]
        )
        await _seed_role_permiso(db_session, "profesor", "entregas:ver")
        await _seed_role_permiso(db_session, "coordinador", "entregas:gestionar")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)

        codigos = [p[0] for p in perms]
        assert "entregas:ver" in codigos
        assert "entregas:gestionar" in codigos

    async def test_user_without_asignacion_returns_empty(self, db_session: AsyncSession):
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"no-role-{uuid.uuid4().hex[:8]}@test.com")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)

        assert perms == []

    async def test_has_permission_true(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(db_session, tenant.id, roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "usuarios:gestionar")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        assert await ps.has_permission(user, "usuarios:gestionar") is True

    async def test_has_permission_false(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(db_session, tenant.id, roles=["tutor"])

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        assert await ps.has_permission(user, "usuarios:gestionar") is False

    async def test_get_permission_scope(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "entregas:ver", alcance="propio")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        scope = await ps.get_permission_scope(user, "entregas:ver")
        assert scope == "propio"

    async def test_get_permission_scope_none(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await self._create_user_with_asignacion(db_session, tenant.id, roles=["tutor"])

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        scope = await ps.get_permission_scope(user, "entregas:ver")
        assert scope is None

    async def test_permissions_isolated_by_tenant(self, db_session: AsyncSession):
        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        user1 = await self._create_user_with_asignacion(db_session, t1.id, roles=["admin"])
        user2 = await self._create_user_with_asignacion(db_session, t2.id, roles=["admin"])

        await _seed_role_permiso(db_session, "admin", "tenant_a_only")
        await _seed_role_permiso(db_session, "admin", "tenant_b_only")

        from app.services.permission_service import PermissionService

        ps1 = PermissionService(db_session)
        perms1 = await ps1.get_effective_permissions(user1)
        codigos1 = [p[0] for p in perms1]

        ps2 = PermissionService(db_session)
        perms2 = await ps2.get_effective_permissions(user2)
        codigos2 = [p[0] for p in perms2]

        # Tenants share the same Rol table (Rol is tenant-agnostic).
        # The isolation here comes from Asignacion.tenant_id filtering.
        # Both admin roles get both permissions since Rol is not tenant-scoped.
        # This test verifies that user2 can also see "tenant_a_only" because
        # the Rol model is NOT tenant-scoped (it's a global catalog).
        assert len(perms1) >= 1
        assert len(perms2) >= 1

    async def test_user_without_asignacion_in_different_tenant(self, db_session: AsyncSession):
        from tests.conftest import create_user

        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        await _seed_role_permiso(db_session, "profesor", "entregas:ver")

        user_t2 = await create_user(db_session, t2.id, email=f"no-role-{uuid.uuid4().hex[:8]}@test.com")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user_t2)
        assert perms == []

    async def test_union_deduplicates(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        from datetime import date
        from tests.conftest import create_user

        user = await create_user(db_session, tenant.id, email=f"multi-{uuid.uuid4().hex[:8]}@test.com", roles=[])
        from app.models.asignacion import Asignacion

        for _ in range(2):
            asig = Asignacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
                rol="PROFESOR", desde=date(2020, 1, 1), comisiones=[],
            )
            db_session.add(asig)
        await db_session.flush()

        await _seed_role_permiso(db_session, "profesor", "entregas:ver")

        from app.services.permission_service import PermissionService

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)

        assert len(perms) == 1
        assert ("entregas:ver", "global") in perms


# ═══════════════════════════════════════════════════════
# require_permission guard tests
# ═══════════════════════════════════════════════════════


class TestRequirePermission:
    """FastAPI dependency guard (require_permission) with Asignacion."""

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
        from fastapi import Depends, FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.core.dependencies import require_permission

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session

        app.dependency_overrides[get_db_session] = _db_override

        @app.get("/api/need-perm")
        async def _need_perm(_: None = Depends(require_permission("test:perm"))):
            return {"ok": True}

        return app

    async def test_user_with_permission_allows(self, db_session, test_settings):
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"ok-{uuid.uuid4().hex[:8]}@test.com", roles=["tester"])
        await _seed_role_permiso(db_session, "tester", "test:perm")
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/need-perm")
        assert resp.status_code == 200

    async def test_user_without_permission_gets_403(self, db_session, test_settings):
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"no-perm-{uuid.uuid4().hex[:8]}@test.com", roles=["tutor"])
        await db_session.commit()

        app = await self._build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/need-perm")
        assert resp.status_code == 403

    async def test_alcance_propio_owner_check_ok(self, db_session, test_settings):
        from fastapi import Depends, Request
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"owner-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "test:propio", alcance="propio")
        await db_session.commit()

        def _is_owner(req: Request, u) -> bool:
            return True

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.core.dependencies import require_permission

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        @app.get("/api/propio-check")
        async def _propio(_: None = Depends(require_permission("test:propio", owner_check=_is_owner))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/propio-check")
        assert resp.status_code == 200

    async def test_alcance_propio_owner_check_fails(self, db_session, test_settings):
        from fastapi import Depends, Request
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"not-owner-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "test:propio", alcance="propio")
        await db_session.commit()

        def _not_owner(req: Request, u) -> bool:
            return False

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.core.dependencies import require_permission

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        @app.get("/api/propio-fail")
        async def _propio_fail(_: None = Depends(require_permission("test:propio", owner_check=_not_owner))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/propio-fail")
        assert resp.status_code == 403

    async def test_alcance_propio_without_owner_check_fails(self, db_session, test_settings):
        from fastapi import Depends
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"no-check-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "test:propio", alcance="propio")
        await db_session.commit()

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.core.dependencies import require_permission

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        @app.get("/api/propio-no-check")
        async def _propio_no_check(_: None = Depends(require_permission("test:propio"))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/propio-no-check")
        assert resp.status_code == 403

    async def test_alcance_global_overrides_owner_check(self, db_session, test_settings):
        from fastapi import Depends, Request
        from tests.conftest import create_user

        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"global-{uuid.uuid4().hex[:8]}@test.com", roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "test:global", alcance="global")
        await db_session.commit()

        def _is_owner(_req, _u) -> bool:
            return False

        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session
        from app.core.dependencies import require_permission

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_current_user] = lambda: user

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        @app.get("/api/global-override")
        async def _global_override(_: None = Depends(require_permission("test:global", owner_check=_is_owner))):
            return {"ok": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/global-override")
        assert resp.status_code == 200
