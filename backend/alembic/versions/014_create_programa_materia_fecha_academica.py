"""014_create_programa_materia_fecha_academica

Creates:
    - programa_materia table
    - fecha_academica table

Revision ID: 014
Revises: 013
Create Date: 2026-06-19 18:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014"
down_revision: Union[str, Sequence[str], None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "programa_materia",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("carrera_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cohorte_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "materia_id", "carrera_id", "cohorte_id",
            name="uq_programa_materia",
        ),
    )
    op.create_index(
        op.f("ix_programa_materia_materia_id"), "programa_materia", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_programa_materia_carrera_id"), "programa_materia", ["carrera_id"], unique=False
    )
    op.create_index(
        op.f("ix_programa_materia_cohorte_id"), "programa_materia", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_programa_materia_tenant_id"), "programa_materia", ["tenant_id"], unique=False
    )

    op.create_table(
        "fecha_academica",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cohorte_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "materia_id", "cohorte_id", "tipo", "numero", "periodo",
            name="uq_fecha_academica",
        ),
    )
    op.create_index(
        op.f("ix_fecha_academica_materia_id"), "fecha_academica", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_fecha_academica_cohorte_id"), "fecha_academica", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_fecha_academica_tenant_id"), "fecha_academica", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_fecha_academica_tenant_id"), table_name="fecha_academica")
    op.drop_index(op.f("ix_fecha_academica_cohorte_id"), table_name="fecha_academica")
    op.drop_index(op.f("ix_fecha_academica_materia_id"), table_name="fecha_academica")
    op.drop_table("fecha_academica")
    op.drop_index(op.f("ix_programa_materia_tenant_id"), table_name="programa_materia")
    op.drop_index(op.f("ix_programa_materia_cohorte_id"), table_name="programa_materia")
    op.drop_index(op.f("ix_programa_materia_carrera_id"), table_name="programa_materia")
    op.drop_index(op.f("ix_programa_materia_materia_id"), table_name="programa_materia")
    op.drop_table("programa_materia")
