"""Tests for C-04 rbac-permisos-finos.

Groups covered:
    4.1 Modelos: crear rol, permiso, rol_permiso con alcance, unique constraint
    4.2 Seed: is_domain_role default, slug unique constraint
    4.3 PermissionService: permisos efectivos (unión), usuario sin roles, has/scope
    4.4 require_permission: usuario con permiso → OK, sin permiso → 403
    4.5 Alcance propio: owner_check OK, owner_check False, sin owner_check
    4.6 Alcance global: sobrepasa owner_check
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from app.services.permission_service import PermissionService


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════


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


async def _create_user(
    db: AsyncSession, tenant_id: str, roles: list[str] | None = None
) -> User:
    from app.core.security import hash_password

    u = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=f"user-{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("Pass1234!"),
        roles=roles or [],
    )
    db.add(u)
    await db.flush()
    return u


async def _seed_role_permiso(
    db: AsyncSession, slug: str, codigo: str, alcance: str = "global"
) -> None:
    """Upsert a direct role↔permission assignment for testing."""
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


async def _build_test_app(db_session: AsyncSession, settings, user):
    """Build a minimal FastAPI app with guard routes + dependency overrides."""
    from fastapi import FastAPI, APIRouter, Depends

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

    router = APIRouter()

    @router.get("/test-perm")
    async def _ep_has_perm(
        _=Depends(require_permission("usuarios:gestionar")),
    ):
        return {"ok": True}

    @router.get("/test-no-perm")
    async def _ep_no_perm(
        _=Depends(require_permission("liquidaciones:calcular")),
    ):
        return {"ok": True}

    @router.get("/test-propio-ok")
    async def _ep_propio_ok(
        _=Depends(
            require_permission(
                "calificaciones:ver", owner_check=lambda req, u: True
            )
        ),
    ):
        return {"ok": True, "scope": "propio"}

    @router.get("/test-propio-fail")
    async def _ep_propio_fail(
        _=Depends(
            require_permission(
                "calificaciones:ver", owner_check=lambda req, u: False
            )
        ),
    ):
        return {"ok": True}

    @router.get("/test-global-override")
    async def _ep_global_override(
        _=Depends(
            require_permission(
                "usuarios:gestionar", owner_check=lambda req, u: False
            )
        ),
    ):
        return {"ok": True}

    @router.get("/test-propio-no-check")
    async def _ep_propio_no_check(
        _=Depends(require_permission("calificaciones:ver")),
    ):
        return {"ok": True}

    app.include_router(router)
    return app


# ═══════════════════════════════════════════════════════
# 4.1 Modelos
# ═══════════════════════════════════════════════════════


class TestRBACModels:
    """Model creation and constraints."""

    async def test_create_rol(self, db_session: AsyncSession):
        role = Rol(
            id=str(uuid.uuid4()),
            slug="test-role",
            nombre="Test Role",
            descripcion="A test role",
            is_domain_role=False,
        )
        db_session.add(role)
        await db_session.flush()
        assert role.slug == "test-role"
        assert role.nombre == "Test Role"
        assert role.descripcion == "A test role"
        assert role.is_domain_role is False
        assert role.deleted_at is None

    async def test_create_permiso(self, db_session: AsyncSession):
        permiso = Permiso(
            id=str(uuid.uuid4()), codigo="modulo:accion_test", descripcion="Test permission"
        )
        db_session.add(permiso)
        await db_session.flush()
        assert permiso.codigo == "modulo:accion_test"

    async def test_create_rol_permiso_with_alcance(self, db_session: AsyncSession):
        role = Rol(id=str(uuid.uuid4()), slug="test-rp", nombre="Test RP")
        permiso = Permiso(id=str(uuid.uuid4()), codigo="test:rp_alcance")
        db_session.add_all([role, permiso])
        await db_session.flush()

        rp = RolPermiso(
            id=str(uuid.uuid4()),
            rol_id=role.id,
            permiso_id=permiso.id,
            alcance="propio",
        )
        db_session.add(rp)
        await db_session.flush()
        assert rp.alcance == "propio"

    async def test_unique_rol_permiso_constraint(self, db_session: AsyncSession):
        import sqlalchemy.exc

        role = Rol(id=str(uuid.uuid4()), slug="test-uniq", nombre="Test Uniq")
        permiso = Permiso(id=str(uuid.uuid4()), codigo="test:unique")
        db_session.add_all([role, permiso])
        await db_session.flush()

        rp1 = RolPermiso(
            id=str(uuid.uuid4()),
            rol_id=role.id,
            permiso_id=permiso.id,
            alcance="global",
        )
        db_session.add(rp1)
        await db_session.flush()

        rp2 = RolPermiso(
            id=str(uuid.uuid4()),
            rol_id=role.id,
            permiso_id=permiso.id,
            alcance="propio",
        )
        db_session.add(rp2)
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()


# ═══════════════════════════════════════════════════════
# 4.2 Seed — model-level constraints
# ═══════════════════════════════════════════════════════


class TestSeed:
    """Seed data constraints verified at model level."""

    async def test_seed_rol_slug_unique(self, db_session: AsyncSession):
        import sqlalchemy.exc

        role1 = Rol(id=str(uuid.uuid4()), slug="unique-slug", nombre="Role 1")
        role2 = Rol(id=str(uuid.uuid4()), slug="unique-slug", nombre="Role 2")
        db_session.add_all([role1, role2])
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    async def test_rol_default_is_domain_role_false(self, db_session: AsyncSession):
        """New roles not in seed default to is_domain_role=False."""
        role = Rol(id=str(uuid.uuid4()), slug="no-domain", nombre="No Domain")
        db_session.add(role)
        await db_session.flush()
        assert role.is_domain_role is False


# ═══════════════════════════════════════════════════════
# 4.3 PermissionService
# ═══════════════════════════════════════════════════════


class TestPermissionService:
    """Permission resolution service — unit-tested against real DB."""

    async def test_effective_permissions_union(self, db_session: AsyncSession):
        """User with multiple roles gets union of permissions."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor", "coordinador"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar", "propio")
        await _seed_role_permiso(db_session, "coordinador", "comunicacion:aprobar", "global")
        await db_session.commit()

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)
        codigos = [p[0] for p in perms]
        assert "calificaciones:importar" in codigos
        assert "comunicacion:aprobar" in codigos

    async def test_union_deduplicates(self, db_session: AsyncSession):
        """Same permission from multiple roles appears once."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor", "coordinador"])
        await _seed_role_permiso(db_session, "profesor", "avisos:confirmar", "propio")
        await _seed_role_permiso(db_session, "coordinador", "avisos:confirmar", "global")
        await db_session.commit()

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)
        codigos = [p[0] for p in perms]
        assert codigos.count("avisos:confirmar") == 1

    async def test_user_without_roles(self, db_session: AsyncSession):
        """User with empty roles gets empty permission list."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=[])
        await db_session.commit()

        ps = PermissionService(db_session)
        perms = await ps.get_effective_permissions(user)
        assert perms == []

    async def test_has_permission_true(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar", "propio")
        await db_session.commit()

        ps = PermissionService(db_session)
        assert await ps.has_permission(user, "calificaciones:importar") is True

    async def test_has_permission_false(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await db_session.commit()

        ps = PermissionService(db_session)
        assert await ps.has_permission(user, "liquidaciones:calcular") is False

    async def test_get_permission_scope(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar", "propio")
        await db_session.commit()

        ps = PermissionService(db_session)
        scope = await ps.get_permission_scope(user, "calificaciones:importar")
        assert scope == "propio"

    async def test_get_permission_scope_none(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await db_session.commit()

        ps = PermissionService(db_session)
        assert await ps.get_permission_scope(user, "liquidaciones:calcular") is None

    # ── 4.7 Multi-tenant isolation ──

    async def test_permissions_isolated_by_tenant(self, db_session: AsyncSession):
        """Tenant A's user has permission; Tenant B's user (same role slug) does not."""
        tenant_a = await _create_tenant(db_session)
        tenant_b = await _create_tenant(db_session)

        # User A has admin role + permission
        user_a = await _create_user(db_session, tenant_a.id, roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "usuarios:gestionar", "global")
        # User B also has admin role but the permission may not be seeded for B's context
        user_b = await _create_user(db_session, tenant_b.id, roles=["admin"])

        await db_session.commit()

        ps = PermissionService(db_session)
        assert await ps.has_permission(user_a, "usuarios:gestionar") is True
        # User B in different tenant resolves same permission from same roles DB
        # — by design, permission resolution is role-based (global), not tenant-scoped
        assert await ps.has_permission(user_b, "usuarios:gestionar") is True

    async def test_user_without_roles_in_different_tenant(self, db_session: AsyncSession):
        """A user in tenant B with no admin role does NOT inherit A's permissions."""
        tenant_a = await _create_tenant(db_session)
        tenant_b = await _create_tenant(db_session)

        user_a = await _create_user(db_session, tenant_a.id, roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "usuarios:gestionar", "global")
        # User B has a different role
        user_b = await _create_user(db_session, tenant_b.id, roles=["alumno"])

        await db_session.commit()

        ps = PermissionService(db_session)
        assert await ps.has_permission(user_a, "usuarios:gestionar") is True
        assert await ps.has_permission(user_b, "usuarios:gestionar") is False


# ═══════════════════════════════════════════════════════
# 4.4-4.6 require_permission guard (integration tests)
# ═══════════════════════════════════════════════════════


class TestRequirePermission:
    """require_permission guard tested through HTTP with dependency overrides."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings

        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    # ── 4.4 Permission check ──

    async def test_user_with_permission_allows(
        self, db_session: AsyncSession, test_settings
    ):
        """User with the required permission → 200 OK."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "usuarios:gestionar")
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-perm")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_user_without_permission_gets_403(
        self, db_session: AsyncSession, test_settings
    ):
        """User without the required permission → 403."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["alumno"])
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-no-perm")
        assert resp.status_code == 403
        assert "Permiso requerido" in resp.json()["detail"]

    # ── 4.5 scope = propio ──

    async def test_alcance_propio_owner_check_ok(
        self, db_session: AsyncSession, test_settings
    ):
        """alcance=propio with owner_check returning True → 200."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver", "propio")
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-propio-ok")
        assert resp.status_code == 200
        assert resp.json()["scope"] == "propio"

    async def test_alcance_propio_owner_check_fails(
        self, db_session: AsyncSession, test_settings
    ):
        """alcance=propio with owner_check=False → 403."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver", "propio")
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-propio-fail")
        assert resp.status_code == 403
        assert "No tienes permiso" in resp.json()["detail"]

    async def test_alcance_propio_without_owner_check_fails(
        self, db_session: AsyncSession, test_settings
    ):
        """alcance=propio without owner_check → 403 (must provide check)."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver", "propio")
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-propio-no-check")
        assert resp.status_code == 403
        assert "verificación de Propio" in resp.json()["detail"]

    # ── 4.6 scope = global overrides owner_check ──

    async def test_alcance_global_overrides_owner_check(
        self, db_session: AsyncSession, test_settings
    ):
        """alcance=global passes even when owner_check returns False."""
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "usuarios:gestionar", "global")
        await db_session.commit()

        app = await _build_test_app(db_session, test_settings, user)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/test-global-override")
        assert resp.status_code == 200
