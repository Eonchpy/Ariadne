import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Load .env from project root before importing app settings
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from app.main import app  # noqa: E402
from app.db import get_db_session  # noqa: E402
from app.models import Base  # noqa: E402
from app.core.cache import get_redis_client  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    from app.config import settings
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url, poolclass=NullPool, future=True)
    return engine


@pytest.fixture(scope="session", autouse=True)
async def ensure_schema(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        await session.rollback()
    # Cleanup tables between tests using a fresh connection
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE fields, tables, sources, users RESTART IDENTITY CASCADE"))


@pytest.fixture
async def redis_client() -> Redis:
    client = get_redis_client()
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def client(db_session: AsyncSession):
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
