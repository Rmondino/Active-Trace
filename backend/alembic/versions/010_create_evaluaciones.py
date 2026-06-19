"""010_create_evaluaciones

Creates:
    - evaluacion table
    - reserva_evaluacion table
    - resultado_evaluacion table
    - Composite indexes for tenant-scoped queries

Revision ID: 010
Revises: 009
Create Date: 2026-06-19 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, Sequence[str], None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── evaluacion ──
    op.create_table(
        "evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default=sa.text("'Coloquio'")),
        sa.Column("instancia", sa.String(length=200), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("cupo_por_dia", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("convocados", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluacion_materia_id"),
        "evaluacion",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluacion_cohorte_id"),
        "evaluacion",
        ["cohorte_id"],
        unique=False,
    )
    op.create_index(
        "ix_evaluacion_tenant_cohorte",
        "evaluacion",
        ["tenant_id", "cohorte_id"],
        unique=False,
    )

    # ── reserva_evaluacion ──
    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.String(length=5), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'Activa'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "evaluacion_id", "alumno_id",
            name="uq_reserva_evaluacion_tenant_evaluacion_alumno",
        ),
    )
    op.create_index(
        op.f("ix_reserva_evaluacion_evaluacion_id"),
        "reserva_evaluacion",
        ["evaluacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reserva_evaluacion_alumno_id"),
        "reserva_evaluacion",
        ["alumno_id"],
        unique=False,
    )
    op.create_index(
        "ix_reserva_evaluacion_tenant_evaluacion",
        "reserva_evaluacion",
        ["tenant_id", "evaluacion_id"],
        unique=False,
    )

    # ── resultado_evaluacion ──
    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("nota_final", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_resultado_evaluacion_evaluacion_id"),
        "resultado_evaluacion",
        ["evaluacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resultado_evaluacion_alumno_id"),
        "resultado_evaluacion",
        ["alumno_id"],
        unique=False,
    )
    op.create_index(
        "ix_resultado_evaluacion_tenant_evaluacion",
        "resultado_evaluacion",
        ["tenant_id", "evaluacion_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resultado_evaluacion_tenant_evaluacion", table_name="resultado_evaluacion")
    op.drop_index(op.f("ix_resultado_evaluacion_evaluacion_id"), table_name="resultado_evaluacion")
    op.drop_index(op.f("ix_resultado_evaluacion_alumno_id"), table_name="resultado_evaluacion")
    op.drop_table("resultado_evaluacion")
    op.drop_index("ix_reserva_evaluacion_tenant_evaluacion", table_name="reserva_evaluacion")
    op.drop_index(op.f("ix_reserva_evaluacion_evaluacion_id"), table_name="reserva_evaluacion")
    op.drop_index(op.f("ix_reserva_evaluacion_alumno_id"), table_name="reserva_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_index("ix_evaluacion_tenant_cohorte", table_name="evaluacion")
    op.drop_index(op.f("ix_evaluacion_materia_id"), table_name="evaluacion")
    op.drop_index(op.f("ix_evaluacion_cohorte_id"), table_name="evaluacion")
    op.drop_table("evaluacion")
