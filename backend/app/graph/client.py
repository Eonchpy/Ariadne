from typing import AsyncIterator
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings


def get_neo4j_driver() -> AsyncDriver:
    return AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )


async def neo4j_dependency() -> AsyncIterator[AsyncDriver]:
    driver = get_neo4j_driver()
    try:
        yield driver
    finally:
        await driver.close()
