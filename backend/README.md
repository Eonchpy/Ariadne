# Ariadne Backend (Phase 1 Scaffold)

## Quick start

1) Create and fill `.env` (use existing root `.env`). Ensure `DATABASE_URL` points to Postgres (async driver is auto-coerced to `postgresql+asyncpg://`).  
2) Install dependencies:
```bash
pip install -e .[dev]
```
3) Run migrations:
```bash
cd backend && alembic upgrade head
```
4) Optional: bootstrap admin user by setting `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` (runs on startup).
5) Run API:
```bash
uvicorn app.main:app --reload
```

## Notes
- Auth: real user lookup via Postgres. Use `ADMIN_EMAIL`/`ADMIN_PASSWORD` to seed an admin on startup; tokens stored in Redis for refresh revocation.
- Source/Table/Field endpoints now use Postgres via SQLAlchemy models/repositories (no longer in-memory).
- Redis/Neo4j clients are wired for future use; Postgres async engine is configured.

## Structure
- `app/main.py` FastAPI app + routers
- `app/config.py` settings from `.env`
- `app/core/*` logging, security, cache helpers
- `app/api/v1/*` HTTP routes (auth, users, sources, tables, fields)
- `app/services/*` temporary business logic stubs
- `app/schemas/*` Pydantic models aligning with OpenAPI v0.1.1
