"""Seed initial tenant + admin user for local development."""

import asyncio
import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.security import encrypt, get_encryption_key, hash_email, hash_password

settings = Settings()
engine = create_async_engine(settings.DATABASE_URL)


async def seed() -> None:
    async with AsyncSession(engine) as session:
        enc_key = get_encryption_key(settings)

        # 1. Create Tenant
        tenant_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO tenant (id, slug, nombre, config, estado, created_at, updated_at)
                VALUES (:id, :slug, :nombre, :config, 'Activo', NOW(), NOW())
                ON CONFLICT (slug) DO NOTHING
            """),
            {
                "id": tenant_id,
                "slug": "universidad-nacional",
                "nombre": "Universidad Nacional",
                "config": '{}',
            },
        )
        print(f"Tenant: {tenant_id}")

        # Get existing tenant if already created
        row = await session.execute(
            text("SELECT id FROM tenant WHERE slug = 'universidad-nacional'"),
        )
        tenant_id = row.scalar()

        # 2. Create Admin User
        email = "admin@universidad.com"
        password = "admin123"
        encrypted_email = encrypt(email, enc_key)
        email_hash = hash_email(email)
        encrypted_dni = encrypt("12345678", enc_key)

        user_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO "user" (id, tenant_id, email_hash, email, password_hash,
                    nombre, apellidos, dni, estado, facturador, two_fa_enabled, created_at, updated_at)
                VALUES (:id, :tenant_id, :email_hash, :email, :password_hash,
                    :nombre, :apellidos, :dni, 'Activo', false, false, NOW(), NOW())
                ON CONFLICT (tenant_id, email_hash) DO NOTHING
            """),
            {
                "id": user_id,
                "tenant_id": tenant_id,
                "email_hash": email_hash,
                "email": encrypted_email,
                "password_hash": hash_password(password),
                "nombre": "Admin",
                "apellidos": "Sistema",
                "dni": encrypted_dni,
            },
        )
        print(f"User: {email} / {password}")

        # Get existing user if already created
        row = await session.execute(
            text("""SELECT id FROM "user" WHERE tenant_id = :t AND email_hash = :e"""),
            {"t": tenant_id, "e": email_hash},
        )
        user_id = row.scalar()

        # 3. Get ADMIN rol id
        row = await session.execute(
            text("SELECT id FROM rol WHERE slug = 'admin'"),
        )
        rol_id = row.scalar()
        if not rol_id:
            print("ERROR: ADMIN rol not found. Run migrations first.")
            return

        # 4. Assign ADMIN role
        await session.execute(
            text("""
                INSERT INTO asignacion (id, tenant_id, usuario_id, rol, comisiones, desde, created_at, updated_at)
                VALUES (:id, :tenant_id, :usuario_id, 'ADMIN', :comisiones, :desde, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "usuario_id": user_id,
                "comisiones": '[]',
                "desde": date.today(),
            },
        )
        print(f"ADMIN role assigned to user {user_id}")

        await session.commit()
        print("\n✅ Seed completo!")
        print(f"   Login: {email}")
        print(f"   Pass:  {password}")


asyncio.run(seed())
