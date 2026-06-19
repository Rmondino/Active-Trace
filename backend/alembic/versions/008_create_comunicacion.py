"""008_create_comunicacion

Creates:
    - comunicacion table
    - Composite indexes for tenant-scoped queries

Revision ID: 008
Revises: 007
Create Date: 2026-06-19 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, Sequence[str], None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comunicacion",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("enviado_por", sa.String(), nullable=False),
        sa.Column("materia_id", sa.String(), nullable=False),
        sa.Column("destinatario", sa.String(), nullable=False),
        sa.Column("asunto", sa.String(), nullable=False),
        sa.Column("cuerpo", sa.String(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("lote_id", sa.String(), nullable=False),
        sa.Column("error_msg", sa.String(), nullable=True),
        sa.Column("aprobado_por", sa.String(), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enviado_por"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["aprobado_por"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comunicacion_lote",
        "comunicacion",
        ["tenant_id", "lote_id"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_estado",
        "comunicacion",
        ["tenant_id", "estado"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_materia",
        "comunicacion",
        ["tenant_id", "materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comunicacion_materia_id"),
        "comunicacion",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comunicacion_lote_id"),
        "comunicacion",
        ["lote_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_comunicacion_lote_id"), table_name="comunicacion")
    op.drop_index(op.f("ix_comunicacion_materia_id"), table_name="comunicacion")
    op.drop_index("ix_comunicacion_materia", table_name="comunicacion")
    op.drop_index("ix_comunicacion_estado", table_name="comunicacion")
    op.drop_index("ix_comunicacion_lote", table_name="comunicacion")
    op.drop_table("comunicacion")
