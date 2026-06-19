"""011_create_aviso_acknowledgment

Creates:
    - aviso table (notices/tablón board)
    - acknowledgment_aviso table (user acknowledgments)
    - Composite indexes and unique constraints

Revision ID: 011
Revises: 010
Create Date: 2026-06-19 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, Sequence[str], None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── aviso ──
    op.create_table(
        "aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alcance", sa.String(length=20), nullable=False, server_default=sa.text("'Global'")),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("rol_destino", sa.String(length=20), nullable=True),
        sa.Column("severidad", sa.String(length=20), nullable=False, server_default=sa.text("'Info'")),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("cuerpo", sa.String(length=5000), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aviso_tenant_id"), "aviso", ["tenant_id"], unique=False)

    # ── acknowledgment_aviso ──
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("aviso_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "aviso_id", "usuario_id",
            name="uq_ack_aviso_tenant_aviso_usuario",
        ),
    )
    op.create_index(
        op.f("ix_acknowledgment_aviso_aviso_id"),
        "acknowledgment_aviso",
        ["aviso_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_acknowledgment_aviso_usuario_id"),
        "acknowledgment_aviso",
        ["usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_acknowledgment_aviso_usuario_id"), table_name="acknowledgment_aviso")
    op.drop_index(op.f("ix_acknowledgment_aviso_aviso_id"), table_name="acknowledgment_aviso")
    op.drop_table("acknowledgment_aviso")
    op.drop_index(op.f("ix_aviso_tenant_id"), table_name="aviso")
    op.drop_table("aviso")
