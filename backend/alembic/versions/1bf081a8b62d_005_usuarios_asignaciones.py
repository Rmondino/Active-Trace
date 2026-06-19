"""005_usuarios_asignaciones

Creates:
    - asignacion table
    - New user profile columns (nombre, apellidos, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, facturador, estado)
    - email_hash + index + unique constraint (tenant_id, email_hash)
    - Data migration: encrypts plaintext emails in the email column
    - Drops: roles JSONB column, ix_user_email index

Revision ID: 1bf081a8b62d
Revises: 7c065d851ca7
Create Date: 2026-06-18 21:56:56.684564
"""

import hashlib
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "1bf081a8b62d"
down_revision: Union[str, Sequence[str], None] = "7c065d851ca7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_encryption_key() -> bytes:
    """Read encryption key from env (used in migration context)."""
    key = os.environ.get("ENCRYPTION_KEY", "")
    if len(key) != 32:
        # Fallback for dev: if no key or wrong size, skip data migration
        return b""
    return key.encode("utf-8")


def _encrypt(plaintext: str, key: bytes) -> str:
    """Minimal AES-256-GCM encrypt for data migration."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    import base64
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def upgrade() -> None:
    conn = op.get_bind()

    # --- Create asignacion table ---
    op.create_table(
        "asignacion",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("usuario_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("rol", sa.String(length=50), nullable=False),
        sa.Column("materia_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("carrera_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("cohorte_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("comisiones", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("responsable_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asignacion_rol"), "asignacion", ["rol"], unique=False)
    op.create_index(op.f("ix_asignacion_tenant_id"), "asignacion", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_asignacion_usuario_id"), "asignacion", ["usuario_id"], unique=False)

    # --- Add new columns to user ---
    op.add_column("user", sa.Column("email_hash", sa.String(length=64), nullable=True))
    op.add_column("user", sa.Column("nombre", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("apellidos", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("dni", sa.String(length=512), nullable=True))
    op.add_column("user", sa.Column("cuil", sa.String(length=512), nullable=True))
    op.add_column("user", sa.Column("cbu", sa.String(length=512), nullable=True))
    op.add_column("user", sa.Column("alias_cbu", sa.String(length=512), nullable=True))
    op.add_column("user", sa.Column("banco", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("regional", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("legajo", sa.String(length=100), nullable=True))
    op.add_column("user", sa.Column("legajo_profesional", sa.String(length=100), nullable=True))
    op.add_column("user", sa.Column("facturador", sa.Boolean(), nullable=True))
    op.add_column("user", sa.Column("estado", sa.String(length=20), nullable=True))

    # --- Data migration: encrypt existing emails ---
    enc_key = _get_encryption_key()
    if enc_key:
        rows = conn.execute(
            text("SELECT id, email, tenant_id FROM \"user\" WHERE email IS NOT NULL")
        ).fetchall()

        for row in rows:
            user_id = row[0]
            plain_email = row[1]
            tenant_id = row[2]
            email_hash = hashlib.sha256(plain_email.lower().encode("utf-8")).hexdigest()
            encrypted = _encrypt(plain_email, enc_key)

            conn.execute(
                text(
                    "UPDATE \"user\" SET "
                    "email = :encrypted, "
                    "email_hash = :email_hash, "
                    "nombre = :nombre, "
                    "apellidos = :apellidos, "
                    "estado = :estado "
                    "WHERE id = :id"
                ).params(
                    id=user_id,
                    encrypted=encrypted,
                    email_hash=email_hash,
                    nombre="",
                    apellidos="",
                    estado="Activo",
                )
            )
    else:
        # No encryption key: set empty defaults for existing rows
        conn.execute(
            text(
                "UPDATE \"user\" SET "
                "email_hash = '', "
                "nombre = '', "
                "apellidos = '', "
                "estado = 'Activo' "
                "WHERE email_hash IS NULL"
            )
        )

    # --- Widen email column to hold base64 ciphertext ---
    op.alter_column(
        "user",
        "email",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.String(length=512),
        existing_nullable=False,
    )

    # --- Remove old email index, drop roles ---
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.create_index(op.f("ix_user_email_hash"), "user", ["email_hash"], unique=False)
    op.drop_column("user", "roles")

    # --- Make new columns NOT NULL now that data is migrated ---
    op.alter_column("user", "email_hash", nullable=False)
    op.alter_column("user", "nombre", nullable=False)
    op.alter_column("user", "apellidos", nullable=False)
    op.alter_column("user", "estado", nullable=False)

    # --- Add unique constraint for (tenant_id, email_hash) ---
    op.create_unique_constraint(
        "uq_user_tenant_email_hash",
        "user",
        ["tenant_id", "email_hash"],
    )

    # --- Set default values for remaining nullable columns ---
    op.alter_column("user", "facturador", server_default=sa.text("false"), nullable=False)


def downgrade() -> None:
    op.drop_constraint("uq_user_tenant_email_hash", "user", type_="unique")
    op.add_column(
        "user",
        sa.Column(
            "roles",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_index(op.f("ix_user_email_hash"), table_name="user")
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=False)
    op.alter_column(
        "user",
        "email",
        existing_type=sa.String(length=512),
        type_=sa.VARCHAR(length=255),
        existing_nullable=False,
    )
    op.drop_column("user", "estado")
    op.drop_column("user", "facturador")
    op.drop_column("user", "legajo_profesional")
    op.drop_column("user", "legajo")
    op.drop_column("user", "regional")
    op.drop_column("user", "banco")
    op.drop_column("user", "alias_cbu")
    op.drop_column("user", "cbu")
    op.drop_column("user", "cuil")
    op.drop_column("user", "dni")
    op.drop_column("user", "apellidos")
    op.drop_column("user", "nombre")
    op.drop_column("user", "email_hash")
    op.drop_index(op.f("ix_asignacion_usuario_id"), table_name="asignacion")
    op.drop_index(op.f("ix_asignacion_tenant_id"), table_name="asignacion")
    op.drop_index(op.f("ix_asignacion_rol"), table_name="asignacion")
    op.drop_table("asignacion")
