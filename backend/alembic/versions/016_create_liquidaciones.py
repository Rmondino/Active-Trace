"""016_create_liquidaciones

Creates:
    - salario_base
    - salario_plus
    - materia_grupo_plus
    - liquidacion
    - factura

Revision ID: 016
Revises: 015
Create Date: 2026-06-19 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "016"
down_revision: Union[str, Sequence[str], None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "salario_base",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_salario_base_rol"), "salario_base", ["rol"], unique=False)
    op.create_index(
        op.f("ix_salario_base_tenant_id"), "salario_base", ["tenant_id"], unique=False
    )

    op.create_table(
        "salario_plus",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", sa.String(50), nullable=True),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("tope_acumulacion", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_salario_plus_grupo"), "salario_plus", ["grupo"], unique=False
    )
    op.create_index(
        op.f("ix_salario_plus_tenant_id"), "salario_plus", ["tenant_id"], unique=False
    )

    op.create_table(
        "materia_grupo_plus",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materia.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_materia_grupo_plus_materia_id"),
        "materia_grupo_plus",
        ["materia_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_materia_grupo_plus_grupo"),
        "materia_grupo_plus",
        ["grupo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_materia_grupo_plus_tenant_id"),
        "materia_grupo_plus",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "liquidacion",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cohorte_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("comisiones", JSONB, nullable=False, server_default="[]"),
        sa.Column("monto_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "excluido_por_factura",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'Abierta'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_liquidacion_cohorte_id"), "liquidacion", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_liquidacion_periodo"), "liquidacion", ["periodo"], unique=False
    )
    op.create_index(
        op.f("ix_liquidacion_usuario_id"), "liquidacion", ["usuario_id"], unique=False
    )
    op.create_index(
        op.f("ix_liquidacion_tenant_id"), "liquidacion", ["tenant_id"], unique=False
    )

    op.create_table(
        "factura",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("usuario_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("referencia_archivo", sa.String(255), nullable=True),
        sa.Column("tamano_kb", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default=sa.text("'Pendiente'")),
        sa.Column("cargada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_factura_usuario_id"), "factura", ["usuario_id"], unique=False
    )
    op.create_index(
        op.f("ix_factura_periodo"), "factura", ["periodo"], unique=False
    )
    op.create_index(
        op.f("ix_factura_tenant_id"), "factura", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_factura_tenant_id"), table_name="factura")
    op.drop_index(op.f("ix_factura_periodo"), table_name="factura")
    op.drop_index(op.f("ix_factura_usuario_id"), table_name="factura")
    op.drop_table("factura")

    op.drop_index(op.f("ix_liquidacion_tenant_id"), table_name="liquidacion")
    op.drop_index(op.f("ix_liquidacion_usuario_id"), table_name="liquidacion")
    op.drop_index(op.f("ix_liquidacion_periodo"), table_name="liquidacion")
    op.drop_index(op.f("ix_liquidacion_cohorte_id"), table_name="liquidacion")
    op.drop_table("liquidacion")

    op.drop_index(op.f("ix_materia_grupo_plus_tenant_id"), table_name="materia_grupo_plus")
    op.drop_index(op.f("ix_materia_grupo_plus_grupo"), table_name="materia_grupo_plus")
    op.drop_index(op.f("ix_materia_grupo_plus_materia_id"), table_name="materia_grupo_plus")
    op.drop_table("materia_grupo_plus")

    op.drop_index(op.f("ix_salario_plus_tenant_id"), table_name="salario_plus")
    op.drop_index(op.f("ix_salario_plus_grupo"), table_name="salario_plus")
    op.drop_table("salario_plus")

    op.drop_index(op.f("ix_salario_base_tenant_id"), table_name="salario_base")
    op.drop_index(op.f("ix_salario_base_rol"), table_name="salario_base")
    op.drop_table("salario_base")
