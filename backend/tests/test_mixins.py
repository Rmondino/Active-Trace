"""Tests for ORM mixins: TimeStamped, SoftDelete, TenantScoped.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


class TestMixins:
    """Verify that mixins behave correctly."""

    @pytest.mark.asyncio
    async def test_timestamps_set_on_create(self, db_session: AsyncSession):
        """created_at and updated_at are set on INSERT."""
        tenant = Tenant(
            id="11111111-1111-1111-1111-111111111121",
            slug="test-ts-tenant",
            nombre="Test Tenant",
        )
        db_session.add(tenant)
        await db_session.flush()
        assert tenant.created_at is not None
        assert tenant.updated_at is not None

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_at(self, db_session: AsyncSession):
        """soft_delete sets deleted_at timestamp."""
        tenant = Tenant(
            id="11111111-1111-1111-1111-111111111122",
            slug="test-sd-tenant",
            nombre="Test Tenant 2",
        )
        db_session.add(tenant)
        await db_session.flush()

        from datetime import UTC, datetime

        tenant.deleted_at = datetime.now(UTC)
        await db_session.flush()

        assert tenant.deleted_at is not None

    @pytest.mark.asyncio
    async def test_restore_clears_deleted_at(self, db_session: AsyncSession):
        """Restore clears deleted_at."""
        tenant = Tenant(
            id="11111111-1111-1111-1111-111111111123",
            slug="test-rest-tenant",
            nombre="Test Tenant 3",
        )
        db_session.add(tenant)
        await db_session.flush()

        from datetime import UTC, datetime

        tenant.deleted_at = datetime.now(UTC)
        await db_session.flush()

        tenant.deleted_at = None
        await db_session.flush()

        assert tenant.deleted_at is None
