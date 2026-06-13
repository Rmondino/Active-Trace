## Why

C-01 dejó el esqueleto ejecutable. El próximo cimiento crítico es el modelo multi-tenant: sin `Tenant` como raíz, sin el mixin de soft delete, sin el repositorio genérico que filtra por `tenant_id`, y sin el cifrado AES-256 para PII, ningún módulo de dominio (usuarios, materias, calificaciones) puede existir de forma segura. Construir estos componentes ahora —cuando no hay datos ni consumidores— evita refactors disruptivos más adelante.

## What Changes

- **Modelo `Tenant`** como entidad raíz del sistema: tabla `tenant` con nombre, slug, configuración y estado.
- **Mixin base** (`TimeStampedMixin`, `SoftDeleteMixin`, `TenantScopedMixin`) que toda tabla del dominio heredará: `id` UUID PK, `tenant_id` FK, `created_at`, `updated_at`, `deleted_at` (soft delete).
- **Repository genérico** (`BaseRepository[ModelT]`) con:
  - CRUD básico (get, list, create, update, soft_delete, restore).
  - **Scope de tenant obligatorio**: todo query filtra por `tenant_id` automáticamente.
  - Soft delete transversal (nunca hard delete).
  - Método `list_all()` que explícitamente salta el scope (solo para uso controlado, ej. seeders).
- **Utilidad de cifrado AES-256** (`core/security.py`) para atributos `[cifrado]`: cifrar/descifrar strings en reposo, con validación de clave de 32 bytes. Nunca exponer datos en logs.
- **Migración Alembic 001**: creación de la tabla `tenant`.
- **Refactor de modelos existentes**: el modelo `Base` de C-01 se completa con los mixins; las tablas futuras heredarán de `Base` con soft delete y tenant scope.
- **Tests obligatorios**:
  - Aislamiento multi-tenant: datos del tenant A invisibles desde el tenant B.
  - Soft delete: `get` no retorna borrados; `list` no los incluye; `restore` los recupera.
  - Cifrado round-trip: cifrar → descifrar = original.
  - Mixin timestamps: `created_at`/`updated_at` se setean automáticamente.

**No hay cambios BREAKING**: C-02 se construye sobre C-01 y no modifica APIs existentes (solo hay `/health`).

## Capabilities

### New Capabilities

- `tenant-model`: Modelo `Tenant`, mixins base (`TimeStampedMixin`, `SoftDeleteMixin`, `TenantScopedMixin`), y el modelo `Base` del ORM.
- `encryption-aes`: Utilidad AES-256 para cifrado/descifrado de PII en reposo, con gestión de clave vía Settings.
- `base-repository`: `BaseRepository[ModelT]` genérico con CRUD, soft delete y scope de tenant automático.
- `migration-001-tenant`: Primera migración Alembic que crea la tabla `tenant`.

### Modified Capabilities

- `app-scaffold`: El modelo `Base` declarativo en `core/database.py` se completa con los mixins. El slot `core/security.py` se llena con la utilidad AES-256. El slot `core/tenancy.py` se llena con la resolución de tenant.

## Impact

- **Nuevo código**: `app/models/tenant.py`, `app/models/mixins.py`, `app/repositories/base.py`, `app/core/crypto.py` (AES-256 en security.py), `app/core/tenancy.py` (resolución de tenant).
- **Modificaciones**: `app/core/database.py` (Base con mixins), `app/core/security.py` (de placeholder a AES-256), `alembic/versions/001_tenant.py`.
- **Tests**: `tests/test_tenant_model.py`, `tests/test_base_repository.py`, `tests/test_encryption.py`.
- **Dependencias**: `cryptography` ya incluida en `pyproject.toml` (C-01). No requiere nuevas dependencias.
- **Habilita** a C-03 (auth-jwt-2fa) y a toda la cadena de Fase 1: sin el modelo Tenant y el repositorio base, ningún otro módulo puede persistir datos.
