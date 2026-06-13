"""Tests for BaseRepository using Tenant model.

Tenant is the root entity — it does NOT have tenant_id.
Tests that check tenant scoping will be added when a model
with TenantScopedMixin exists (e.g., C-06 academic structure).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Concrete repository for Tenant model (for testing)."""
    model_class = Tenant


class TestBaseRepository:
    """Verify BaseRepository CRUD on Tenant model."""

    @pytest.mark.asyncio
    async def test_create_and_get(self, db_session: AsyncSession):
        """Create a tenant and retrieve it by ID."""
        repo = TenantRepository(session=db_session, tenant_id="")
        created = await repo.create({
            "id": "00000000-0000-0000-0000-000000000101",
            "slug": "create-get-tenant",
            "nombre": "Create Get Tenant",
        })
        assert created.id == "00000000-0000-0000-0000-000000000101"

        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.nombre == "Create Get Tenant"

    @pytest.mark.asyncio
    async def test_list_returns_records(self, db_session: AsyncSession):
        """list() returns created records."""
        repo = TenantRepository(session=db_session, tenant_id="")
        await repo.create({
            "id": "00000000-0000-0000-0000-000000000102",
            "slug": "list-tenant-1",
            "nombre": "List Tenant 1",
        })
        await repo.create({
            "id": "00000000-0000-0000-0000-000000000103",
            "slug": "list-tenant-2",
            "nombre": "List Tenant 2",
        })

        records = await repo.list()
        assert len(records) >= 2

    @pytest.mark.asyncio
    async def test_update_record(self, db_session: AsyncSession):
        """update() modifies a record and returns it."""
        repo = TenantRepository(session=db_session, tenant_id="")
        created = await repo.create({
            "id": "00000000-0000-0000-0000-000000000104",
            "slug": "update-tenant",
            "nombre": "Original Name",
        })

        updated = await repo.update(created.id, {"nombre": "Updated Name"})
        assert updated is not None
        assert updated.nombre == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_returns_none_if_not_found(self, db_session: AsyncSession):
        """update() returns None when ID does not exist."""
        repo = TenantRepository(session=db_session, tenant_id="")
        result = await repo.update(
            "00000000-0000-0000-0000-000000099999",
            {"nombre": "Nope"},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_soft_delete_excludes_from_get(self, db_session: AsyncSession):
        """After soft_delete, get() returns None."""
        repo = TenantRepository(session=db_session, tenant_id="")
        created = await repo.create({
            "id": "00000000-0000-0000-0000-000000000105",
            "slug": "sd-get-tenant",
            "nombre": "SD Get Tenant",
        })
        await repo.soft_delete(created.id)
        result = await repo.get(created.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_restore_makes_visible_again(self, db_session: AsyncSession):
        """After restore, get() returns the record."""
        repo = TenantRepository(session=db_session, tenant_id="")
        created = await repo.create({
            "id": "00000000-0000-0000-0000-000000000106",
            "slug": "restore-tenant",
            "nombre": "Restore Test",
        })
        await repo.soft_delete(created.id)
        await repo.restore(created.id)
        result = await repo.get(created.id)
        assert result is not None
        assert result.id == "00000000-0000-0000-0000-000000000106"

    @pytest.mark.asyncio
    async def test_list_all_returns_all(self, db_session: AsyncSession):
        """list_all() returns records."""
        repo = TenantRepository(session=db_session, tenant_id="")
        await repo.create({
            "id": "00000000-0000-0000-0000-000000000107",
            "slug": "list-all-t1",
            "nombre": "List All 1",
        })
        await repo.create({
            "id": "00000000-0000-0000-0000-000000000108",
            "slug": "list-all-t2",
            "nombre": "List All 2",
        })

        all_records = await repo.list_all()
        ids = [r.id for r in all_records]
        assert "00000000-0000-0000-0000-000000000107" in ids
        assert "00000000-0000-0000-0000-000000000108" in ids
