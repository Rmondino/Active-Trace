"""001_create_tenant: Create the tenant table.

Revision ID: 98edada8e066
Revises:
Create Date: 2026-06-03

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "98edada8e066"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("slug", sa.String(120), unique=True, nullable=False, index=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=True, default={}),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Activo",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("tenant")
