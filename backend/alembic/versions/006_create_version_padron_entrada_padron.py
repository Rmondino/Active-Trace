"""006_create_version_padron_entrada_padron

Creates:
    - version_padron table
    - entrada_padron table
    - audit_log table
    - Partial unique index for single active version per (tenant, materia, cohorte)

Revision ID: 006
Revises: 1bf081a8b62d
Create Date: 2026-06-18 23:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "1bf081a8b62d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- version_padron ---
    op.create_table(
        "version_padron",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cohorte_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cargado_por", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("total_filas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cargado_por"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_version_padron_materia_id"), "version_padron", ["materia_id"], unique=False
    )
    op.create_index(
        op.f("ix_version_padron_cohorte_id"), "version_padron", ["cohorte_id"], unique=False
    )
    op.create_index(
        op.f("ix_version_padron_tenant_id"), "version_padron", ["tenant_id"], unique=False
    )
    # Partial unique index: only one active version per (tenant, materia, cohorte)
    op.create_index(
        "ix_version_padron_activa_unique",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=True,
        postgresql_where=sa.text("activa = true AND deleted_at IS NULL"),
    )
    # Composite index for lookup by materia+cohorte
    op.create_index(
        "ix_version_padron_materia_cohorte",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=False,
    )

    # --- entrada_padron ---
    op.create_table(
        "entrada_padron",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("version_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("usuario_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("apellidos", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=512), nullable=False),
        sa.Column("comision", sa.String(length=50), nullable=True),
        sa.Column("regional", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["version_padron.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_entrada_padron_version_id"), "entrada_padron", ["version_id"], unique=False
    )
    op.create_index(
        op.f("ix_entrada_padron_usuario_id"), "entrada_padron", ["usuario_id"], unique=False
    )
    op.create_index(
        op.f("ix_entrada_padron_tenant_id"), "entrada_padron", ["tenant_id"], unique=False
    )
    # Composite index for version lookups within tenant
    op.create_index(
        "ix_entrada_padron_tenant_version",
        "entrada_padron",
        ["tenant_id", "version_id"],
        unique=False,
    )

    # --- audit_log ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("actor_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("accion", sa.String(length=100), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("detalle", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_actor_id"), "audit_log", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_log_tenant_id"), "audit_log", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_audit_log_accion"), "audit_log", ["accion"], unique=False)
    op.create_index(
        op.f("ix_audit_log_materia_id"), "audit_log", ["materia_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_materia_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_accion"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_tenant_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_actor_id"), table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_entrada_padron_tenant_version", table_name="entrada_padron")
    op.drop_index(op.f("ix_entrada_padron_tenant_id"), table_name="entrada_padron")
    op.drop_index(op.f("ix_entrada_padron_usuario_id"), table_name="entrada_padron")
    op.drop_index(op.f("ix_entrada_padron_version_id"), table_name="entrada_padron")
    op.drop_table("entrada_padron")
    op.drop_index("ix_version_padron_materia_cohorte", table_name="version_padron")
    op.drop_index("ix_version_padron_activa_unique", table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_tenant_id"), table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_cohorte_id"), table_name="version_padron")
    op.drop_index(op.f("ix_version_padron_materia_id"), table_name="version_padron")
    op.drop_table("version_padron")
