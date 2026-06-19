"""009_create_slot_instancia_guardia

Creates:
    - slot_encuentro table
    - instancia_encuentro table
    - guardia table
    - Composite indexes for tenant-scoped queries

Revision ID: 009
Revises: 008
Create Date: 2026-06-19 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, Sequence[str], None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── slot_encuentro ──
    op.create_table(
        "slot_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("hora", sa.String(length=5), nullable=False),
        sa.Column("dia_semana", sa.String(length=10), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("cant_semanas", sa.Integer(), nullable=True),
        sa.Column("fecha_unica", sa.Date(), nullable=True),
        sa.Column("meet_url", sa.String(length=500), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_slot_encuentro_materia_id"),
        "slot_encuentro",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        "ix_slot_encuentro_tenant_materia",
        "slot_encuentro",
        ["tenant_id", "materia_id"],
        unique=False,
    )

    # ── instancia_encuentro ──
    op.create_table(
        "instancia_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slot_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.String(length=5), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'Programado'")),
        sa.Column("meet_url", sa.String(length=500), nullable=True),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("comentario", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["slot_encuentro.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_instancia_encuentro_materia_id"),
        "instancia_encuentro",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_materia",
        "instancia_encuentro",
        ["tenant_id", "materia_id"],
        unique=False,
    )
    op.create_index(
        "ix_instancia_encuentro_slot",
        "instancia_encuentro",
        ["slot_id"],
        unique=False,
    )

    # ── guardia ──
    op.create_table(
        "guardia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("dia", sa.String(length=10), nullable=False),
        sa.Column("horario", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("comentarios", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guardia_materia_id"),
        "guardia",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        "ix_guardia_tenant_materia",
        "guardia",
        ["tenant_id", "materia_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_guardia_tenant_materia", table_name="guardia")
    op.drop_index(op.f("ix_guardia_materia_id"), table_name="guardia")
    op.drop_table("guardia")
    op.drop_index("ix_instancia_encuentro_slot", table_name="instancia_encuentro")
    op.drop_index("ix_instancia_encuentro_tenant_materia", table_name="instancia_encuentro")
    op.drop_index(op.f("ix_instancia_encuentro_materia_id"), table_name="instancia_encuentro")
    op.drop_table("instancia_encuentro")
    op.drop_index("ix_slot_encuentro_tenant_materia", table_name="slot_encuentro")
    op.drop_index(op.f("ix_slot_encuentro_materia_id"), table_name="slot_encuentro")
    op.drop_table("slot_encuentro")
