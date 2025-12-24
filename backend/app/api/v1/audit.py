from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repositories.audit_repo import ConnectionTestLogRepository
from app.models.audit import ConnectionTestLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/connection-tests")
async def list_connection_tests(
    source_id: str | None = None,
    limit: int = 100,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    repo = ConnectionTestLogRepository(session)
    logs = await repo.list_by_source(source_id=source_id, limit=limit)
    return [
        {
            "id": str(log.id),
            "source_id": str(log.source_id) if log.source_id else None,
            "operation": log.operation,
            "table_name": log.table_name,
            "tested_by": log.tested_by,
            "result": log.result,
            "error_message": log.error_message,
            "created_at": log.created_at,
        }
        for log in logs
    ]
