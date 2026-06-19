Link del video Active trace "https://youtu.be/wNr-VkIbuu0"

# activia-trace

Plataforma de gestión académica y trazabilidad multi-tenant. Opera como capa de orquestación sobre Moodle: consolida calificaciones, detecta atrasos, gestiona comunicación saliente con aprobación, equipos docentes, encuentros, coloquios, liquidaciones de honorarios y auditoría completa.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.13 + FastAPI async + SQLAlchemy 2.0 + PostgreSQL |
| Frontend | React 18 + TypeScript + Vite + TanStack Query + Tailwind CSS |
| Auth | JWT (access + refresh rotation) + Argon2id + 2FA TOTP |
| Infra | Docker + docker-compose |

## Requisitos

- Docker + docker-compose
- Node.js 18+ (para frontend fuera de Docker)
- OpenSSL (para generar ENCRYPTION_KEY)

## Levantar el proyecto

```bash
# 1. Clonar
git clone https://github.com/Rmondino/Active-Trace.git
cd Active-Trace

# 2. Variables de entorno
echo 'ENCRYPTION_KEY="'"$(openssl rand -hex 16)"'"' > .env

# 3. Copiar config de backend
cp backend/.env.example backend/.env
# Editar ENCRYPTION_KEY en backend/.env con el mismo valor generado arriba

# 4. Levantar servicios
docker compose up -d

# 5. Correr migraciones
docker compose exec api alembic upgrade head

# 6. Seed de datos iniciales (admin + demo)
docker compose exec api python seed.py
docker compose exec api python demo_seed.py

# 7. Frontend
cd frontend && npm install && npm run dev
```

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin@universidad.com` | `admin123` | ADMIN (estructura, usuarios, auditoría, finanzas) |
| `juan@universidad.com` | `juan123` | PROFESOR (Programación I + II) |
| `maria@universidad.com` | `maria123` | PROFESOR (Base de Datos + Inglés) |
| `carlos@universidad.com` | `carlos123` | TUTOR (Programación I) |

## URLs

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

## Comandos útiles

```bash
# Logs del backend
docker compose logs api -f

# Resetear base de datos
docker compose down -v && docker compose up -d && docker compose exec api alembic upgrade head

# Correr tests
docker compose exec api pytest

# Migraciones
docker compose exec api alembic upgrade head
docker compose exec api alembic history
```

## Cambios realizados sobre el repositorio base

- AGENTS.md y CLAUDE.md: reglas duras, governance por dominio, roadmap de 24 changes
- Knowledge Base: 11 archivos, PA-22/PA-23 resueltas (mapeo materia→grupo de Plus y acumulación)
- `openspec/changes/archive/`: 24 changes archivados con proposal, design, specs, tasks
- Skills instaladas: fastapi-templates, python-testing-patterns, tdd, postgresql-table-design, etc.
- Engram: memoria persistente del proyecto compartida entre agentes vía `.engram/`

## Proyecto completo

24/24 changes implementados. 26 routers backend, 8 features frontend, migraciones Alembic, tests.