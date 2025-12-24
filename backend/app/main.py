from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import configure_logging
from app.api.v1 import auth, users, sources, tables, fields, audit, lineage, bulk, tags
from app.db import SessionLocal
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.core.security import get_password_hash
from app.graph.client import get_neo4j_driver, ensure_constraints
import structlog


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: bootstrap admin user if configured
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        async with SessionLocal() as session:
            repo = UserRepository(session)
            existing = await repo.get_by_email(settings.ADMIN_EMAIL)
            if not existing:
                user = User(
                    email=settings.ADMIN_EMAIL,
                    name="Admin",
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    roles=["admin"],
                )
                await repo.add(user)
                await session.commit()
                logger.info("bootstrap_admin_created", email=settings.ADMIN_EMAIL)
    # Startup: ensure Neo4j constraints (best-effort)
    try:
        driver = get_neo4j_driver()
        await ensure_constraints(driver)
        await driver.close()
        logger.info("neo4j_constraints_ensured")
    except Exception as exc:  # pragma: no cover - external service
        logger.warning("neo4j_constraint_init_failed", error=str(exc))
    yield
    # Shutdown: nothing yet


def create_app() -> FastAPI:
    configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

    origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(users.router, prefix=api_prefix)
    app.include_router(sources.router, prefix=api_prefix)
    app.include_router(tables.router, prefix=api_prefix)
    app.include_router(fields.router, prefix=api_prefix)
    app.include_router(audit.router, prefix=api_prefix)
    app.include_router(lineage.router, prefix=api_prefix)
    app.include_router(bulk.router, prefix=api_prefix)
    app.include_router(tags.router, prefix=api_prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
