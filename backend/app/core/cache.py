from typing import AsyncIterator
from redis.asyncio import Redis

from app.config import settings


def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=settings.REDIS_POOL_SIZE,
    )


async def redis_dependency() -> AsyncIterator[Redis]:
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()
