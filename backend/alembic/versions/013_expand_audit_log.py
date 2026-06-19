"""013_expand_audit_log

Adds impersonado_id, user_agent, filas_afectadas columns to audit_log.
Adds indexes for impersonado_id and created_at.

Revision ID: 013
Revises: 012
Create Date: 2026-06-19 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, Sequence[str], None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_log",
        sa.Column("impersonado_id", sa.String(), nullable=True),
    )
    op.add_column(
        "audit_log",
        sa.Column("user_agent", sa.String(255), nullable=True),
    )
    op.add_column(
        "audit_log",
        sa.Column("filas_afectadas", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_audit_log_impersonado_id"),
        "audit_log",
        ["impersonado_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_log_created_at"),
        "audit_log",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_created_at"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_impersonado_id"), table_name="audit_log")
    op.drop_column("audit_log", "filas_afectadas")
    op.drop_column("audit_log", "user_agent")
    op.drop_column("audit_log", "impersonado_id")
