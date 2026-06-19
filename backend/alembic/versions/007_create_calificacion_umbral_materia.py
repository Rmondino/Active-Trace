"""007_create_calificacion_umbral_materia

Creates:
    - calificacion table
    - umbral_materia table

Revision ID: 007
Revises: 006
Create Date: 2026-06-18 23:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, Sequence[str], None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calificacion",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("entrada_padron_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("actividad", sa.String(length=200), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(8, 2), nullable=True),
        sa.Column("nota_textual", sa.String(length=100), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("importado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "entrada_padron_id", "actividad",
            name="uq_calificacion_entrada_actividad",
        ),
    )
    op.create_index(
        op.f("ix_calificacion_entrada_padron_id"), "calificacion", ["entrada_padron_id"], unique=False
    )
    op.create_index(
        op.f("ix_calificacion_materia_id"), "calificacion", ["materia_id"], unique=False
    )
    op.create_index(
        "ix_calificacion_tenant_materia",
        "calificacion",
        ["tenant_id", "materia_id"],
        unique=False,
    )

    op.create_table(
        "umbral_materia",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("asignacion_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("valores_aprobatorios", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uq_umbral_asignacion_materia",
        ),
    )
    op.create_index(
        op.f("ix_umbral_materia_asignacion_id"), "umbral_materia", ["asignacion_id"], unique=False
    )
    op.create_index(
        op.f("ix_umbral_materia_materia_id"), "umbral_materia", ["materia_id"], unique=False
    )
    op.create_index(
        "ix_umbral_tenant_materia",
        "umbral_materia",
        ["tenant_id", "materia_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_umbral_tenant_materia", table_name="umbral_materia")
    op.drop_index(op.f("ix_umbral_materia_materia_id"), table_name="umbral_materia")
    op.drop_index(op.f("ix_umbral_materia_asignacion_id"), table_name="umbral_materia")
    op.drop_table("umbral_materia")
    op.drop_index("ix_calificacion_tenant_materia", table_name="calificacion")
    op.drop_index(op.f("ix_calificacion_materia_id"), table_name="calificacion")
    op.drop_index(op.f("ix_calificacion_entrada_padron_id"), table_name="calificacion")
    op.drop_table("calificacion")
