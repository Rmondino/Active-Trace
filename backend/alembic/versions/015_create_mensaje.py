"""015_create_mensaje

Creates:
    - mensaje table

Revision ID: 015
Revises: 014
Create Date: 2026-06-19 19:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015"
down_revision: Union[str, Sequence[str], None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensaje",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("remitente_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("destinatario_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("mensaje_padre_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("asunto", sa.String(200), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("leido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("leido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["remitente_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destinatario_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mensaje_padre_id"], ["mensaje.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mensaje_remitente_id"), "mensaje", ["remitente_id"], unique=False
    )
    op.create_index(
        op.f("ix_mensaje_destinatario_id"), "mensaje", ["destinatario_id"], unique=False
    )
    op.create_index(
        op.f("ix_mensaje_tenant_id"), "mensaje", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mensaje_tenant_id"), table_name="mensaje")
    op.drop_index(op.f("ix_mensaje_destinatario_id"), table_name="mensaje")
    op.drop_index(op.f("ix_mensaje_remitente_id"), table_name="mensaje")
    op.drop_table("mensaje")
