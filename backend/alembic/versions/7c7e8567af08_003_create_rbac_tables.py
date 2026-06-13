"""003_create_rbac_tables

Revision ID: 7c7e8567af08
Revises: b76cccda4d09
Create Date: 2026-06-03 11:23:14.727725

Creates:
    - rol: domain role catalog
    - permiso: atomic permissions (modulo:accion)
    - rol_permiso: many-to-many role→permission assignment with alcance

Seeds:
    - 7 domain roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS)
    - 22 base permissions (modulo:accion)
    - Complete role↔permission matrix from KB §3.3
"""

import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "7c7e8567af08"
down_revision: Union[str, Sequence[str], None] = "b76cccda4d09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# ── Tables ──


def upgrade() -> None:
    # --- Create tables ---
    op.create_table(
        "rol",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("is_domain_role", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "permiso",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("codigo", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "rol_permiso",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("rol_id", UUID(as_uuid=False), sa.ForeignKey("rol.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("permiso_id", UUID(as_uuid=False), sa.ForeignKey("permiso.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("alcance", sa.String(10), nullable=False, server_default="global"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),
    )

    # --- Seed: 7 domain roles ---
    now = _now()
    roles = [
        ("alumno", "ALUMNO", "Estudiante que cursa materias"),
        ("tutor", "TUTOR", "Auxiliar / ayudante de cátedra"),
        ("profesor", "PROFESOR", "Docente a cargo de comisiones"),
        ("coordinador", "COORDINADOR", "Responsable de materias o cohorte"),
        ("nexo", "NEXO", "Articulación / enlace transversal"),
        ("admin", "ADMIN", "Administrador del sistema dentro del tenant"),
        ("finanzas", "FINANZAS", "Responsable de liquidaciones y honorarios"),
    ]
    role_ids = {}
    for slug, nombre, desc in roles:
        rid = _uid()
        op.execute(
            sa.text(
                "INSERT INTO rol (id, slug, nombre, descripcion, is_domain_role, created_at, updated_at) "
                "VALUES (:id, :slug, :nombre, :descripcion, TRUE, :now, :now) "
                "ON CONFLICT (slug) DO NOTHING"
            ).params(id=rid, slug=slug, nombre=nombre, descripcion=desc, now=now)
        )
        role_ids[slug] = rid

    # --- Seed: 22 base permissions ---
    base_permisos = [
        ("calificaciones:importar", "Importar calificaciones de alumnos"),
        ("atrasados:ver", "Ver alumnos atrasados"),
        ("entregas:ver_sin_corregir", "Ver entregas sin corregir"),
        ("comunicacion:enviar", "Enviar comunicaciones a alumnos"),
        ("comunicacion:aprobar", "Aprobar comunicaciones masivas"),
        ("encuentros:gestionar", "Gestionar encuentros y guardias"),
        ("guardias:registrar", "Registrar guardias"),
        ("tareas:gestionar", "Gestionar tareas internas"),
        ("avisos:publicar", "Publicar avisos"),
        ("equipos:asignar", "Gestionar equipos docentes"),
        ("estructura:gestionar", "Gestionar estructura académica"),
        ("usuarios:gestionar", "Gestionar usuarios del tenant"),
        ("auditoria:ver", "Ver registros de auditoría"),
        ("grilla:operar", "Operar grilla salarial"),
        ("liquidaciones:calcular", "Calcular y cerrar liquidaciones"),
        ("facturas:gestionar", "Gestionar facturas"),
        ("configuracion:gestionar", "Configurar el tenant"),
        ("impersonacion:usar", "Usar impersonación"),
        ("rbac:gestionar", "Gestionar roles y permisos"),
        ("perfil:ver", "Ver estado académico propio"),
        ("evaluaciones:reservar", "Reservar instancias de evaluación"),
        ("avisos:confirmar", "Confirmar avisos (acknowledgment)"),
    ]
    permiso_ids = {}
    for codigo, desc in base_permisos:
        pid = _uid()
        op.execute(
            sa.text(
                "INSERT INTO permiso (id, codigo, descripcion, created_at, updated_at) "
                "VALUES (:id, :codigo, :descripcion, :now, :now) "
                "ON CONFLICT (codigo) DO NOTHING"
            ).params(id=pid, codigo=codigo, descripcion=desc, now=now)
        )
        permiso_ids[codigo] = pid

    # --- Seed: role↔permission matrix (KB §3.3) ---
    # (rol_slug, permiso_codigo, alcance)
    matrix = [
        # ALUMNO
        ("alumno", "perfil:ver", "global"),
        ("alumno", "evaluaciones:reservar", "global"),
        ("alumno", "avisos:confirmar", "global"),
        # TUTOR
        ("tutor", "avisos:confirmar", "global"),
        ("tutor", "atrasados:ver", "global"),
        ("tutor", "entregas:ver_sin_corregir", "global"),
        ("tutor", "encuentros:gestionar", "global"),
        ("tutor", "guardias:registrar", "propio"),
        # PROFESOR
        ("profesor", "avisos:confirmar", "global"),
        ("profesor", "calificaciones:importar", "propio"),
        ("profesor", "atrasados:ver", "propio"),
        ("profesor", "entregas:ver_sin_corregir", "propio"),
        ("profesor", "comunicacion:enviar", "propio"),
        ("profesor", "encuentros:gestionar", "propio"),
        ("profesor", "guardias:registrar", "propio"),
        ("profesor", "tareas:gestionar", "propio"),
        # COORDINADOR
        ("coordinador", "avisos:confirmar", "global"),
        ("coordinador", "calificaciones:importar", "global"),
        ("coordinador", "atrasados:ver", "global"),
        ("coordinador", "entregas:ver_sin_corregir", "global"),
        ("coordinador", "comunicacion:enviar", "global"),
        ("coordinador", "comunicacion:aprobar", "global"),
        ("coordinador", "encuentros:gestionar", "global"),
        ("coordinador", "guardias:registrar", "global"),
        ("coordinador", "tareas:gestionar", "global"),
        ("coordinador", "avisos:publicar", "global"),
        ("coordinador", "equipos:asignar", "global"),
        ("coordinador", "auditoria:ver", "propio"),
        # ADMIN
        ("admin", "avisos:confirmar", "global"),
        ("admin", "calificaciones:importar", "global"),
        ("admin", "atrasados:ver", "global"),
        ("admin", "entregas:ver_sin_corregir", "global"),
        ("admin", "comunicacion:enviar", "global"),
        ("admin", "comunicacion:aprobar", "global"),
        ("admin", "encuentros:gestionar", "global"),
        ("admin", "guardias:registrar", "global"),
        ("admin", "tareas:gestionar", "global"),
        ("admin", "avisos:publicar", "global"),
        ("admin", "equipos:asignar", "global"),
        ("admin", "estructura:gestionar", "global"),
        ("admin", "usuarios:gestionar", "global"),
        ("admin", "auditoria:ver", "global"),
        ("admin", "configuracion:gestionar", "global"),
        ("admin", "impersonacion:usar", "global"),
        ("admin", "rbac:gestionar", "global"),
        # FINANZAS
        ("finanzas", "avisos:confirmar", "global"),
        ("finanzas", "auditoria:ver", "global"),
        ("finanzas", "grilla:operar", "global"),
        ("finanzas", "liquidaciones:calcular", "global"),
        ("finanzas", "facturas:gestionar", "global"),
    ]

    for slug, codigo, alcance in matrix:
        op.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, rol_id, permiso_id, alcance, created_at, updated_at) "
                "VALUES (:id, :rol_id, :permiso_id, :alcance, :now, :now) "
                "ON CONFLICT (rol_id, permiso_id) DO NOTHING"
            ).params(
                id=_uid(),
                rol_id=role_ids[slug],
                permiso_id=permiso_ids[codigo],
                alcance=alcance,
                now=now,
            )
        )


def downgrade() -> None:
    op.drop_table("rol_permiso")
    op.drop_table("permiso")
    op.drop_table("rol")
