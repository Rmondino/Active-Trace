"""012_create_tarea_comentario_tarea

Creates:
    - tarea table (internal task assignments)
    - comentario_tarea table (comments on tasks)
    - Composite indexes for multi-tenant queries

Revision ID: 012
Revises: 011
Create Date: 2026-06-19 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, Sequence[str], None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tarea ──
    op.create_table(
        "tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("asignado_a", sa.Uuid(), nullable=False),
        sa.Column("asignado_por", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("descripcion", sa.String(length=5000), nullable=False),
        sa.Column("contexto_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asignado_a"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignado_por"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tarea_tenant_id"), "tarea", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tarea_asignado_a"), "tarea", ["asignado_a"], unique=False)
    op.create_index(
        "ix_tarea_tenant_estado", "tarea",
        ["tenant_id", "estado"], unique=False,
    )
    op.create_index(
        "ix_tarea_tenant_asignado", "tarea",
        ["tenant_id", "asignado_a"], unique=False,
    )

    # ── comentario_tarea ──
    op.create_table(
        "comentario_tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tarea_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tarea.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comentario_tarea_tarea_id"),
        "comentario_tarea",
        ["tarea_id"], unique=False,
    )
    op.create_index(
        "ix_comentario_tarea_tenant_tarea",
        "comentario_tarea",
        ["tenant_id", "tarea_id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comentario_tarea_tenant_tarea", table_name="comentario_tarea")
    op.drop_index(op.f("ix_comentario_tarea_tarea_id"), table_name="comentario_tarea")
    op.drop_table("comentario_tarea")
    op.drop_index("ix_tarea_tenant_asignado", table_name="tarea")
    op.drop_index("ix_tarea_tenant_estado", table_name="tarea")
    op.drop_index(op.f("ix_tarea_asignado_a"), table_name="tarea")
    op.drop_index(op.f("ix_tarea_tenant_id"), table_name="tarea")
    op.drop_table("tarea")
