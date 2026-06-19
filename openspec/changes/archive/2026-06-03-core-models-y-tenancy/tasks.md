## 1. Modelo Tenant y mixins ORM

- [x] 1.1 Implementar `app/models/mixins.py` con `TimeStampedMixin`, `SoftDeleteMixin` y `TenantScopedMixin` usando SQLAlchemy 2.0 declarative mixins
- [x] 1.2 Implementar `app/models/tenant.py` con el modelo `Tenant` (id UUID, slug único, nombre, config JSONB, estado, timestamps)
- [x] 1.3 Completar `Base` en `core/database.py` integrando los tres mixins y UUID PK; ajustar imports existentes

## 2. Cifrado AES-256 (core/security.py)

- [x] 2.1 Implementar `encrypt(plaintext: str, key: bytes) -> str` y `decrypt(ciphertext: str, key: bytes) -> str` usando AES-256-GCM con nonce aleatorio; output en base64
- [x] 2.2 Conectar la utilidad con `Settings.ENCRYPTION_KEY` y validar clave de exactamente 32 bytes

## 3. Resolución de tenant (core/tenancy.py)

- [x] 3.1 Implementar `core/tenancy.py` con función `get_tenant_context()` y dependencia FastAPI `get_tenant` que resuelve el tenant_id desde el contexto (por ahora desde settings/session, preparado para JWT en C-03)
- [x] 3.2 Integrar la dependencia `get_tenant` con el patrón de inyección de `core/dependencies.py`

## 4. BaseRepository genérico (repositories/base.py)

- [x] 4.1 Implementar `BaseRepository[ModelT]` genérico con: get, list, create, update, soft_delete, restore
- [x] 4.2 Implementar filtro automático de tenant_id en todos los métodos de lectura (get, list) y escritura (create asigna tenant_id)
- [x] 4.3 Implementar `list_all()` que salta el scope de tenant (uso explícito)

## 5. Migración Alembic 001 — tenant

- [x] 5.1 Generar y escribir la migración Alembic 001 que crea la tabla `tenant` con índice único en `slug`
- [x] 5.2 Ejecutar `alembic upgrade head` y verificar que la tabla tenant existe

## 6. Tests

- [x] 6.1 (RED) Escribir tests de mixins: timestamps automáticos, soft delete, restore, herencia correcta
- [x] 6.2 (GREEN) Ajustar modelos hasta que los tests de mixins pasen
- [x] 6.3 (RED) Escribir tests de cifrado round-trip: cifrar→descifrar = original, nonce único, clave incorrecta falla
- [x] 6.4 (GREEN) Implementar/ajustar crypto hasta que los tests pasen
- [x] 6.5 (RED) Escribir tests de `BaseRepository`: get con scope, list con scope, create asigna tenant, update con scope, soft_delete, restore, list_all salta scope
- [x] 6.6 (GREEN) Implementar/ajustar repositorio hasta que los tests pasen
- [x] 6.7 (TRIANGULATE) Escribir test de aislamiento multi-tenant: datos del tenant A no visibles desde tenant B
- [x] 6.8 Ejecutar suite completa de tests y confirmar verde

## 7. Verificación final

- [x] 7.1 Confirmar que el slot `core/tenancy.py` ya no es placeholder y tiene la lógica de resolución de tenant
- [x] 7.2 Confirmar que `core/security.py` ya no es placeholder y tiene la utilidad AES-256
- [x] 7.3 Confirmar que ningún archivo supera 500 LOC
