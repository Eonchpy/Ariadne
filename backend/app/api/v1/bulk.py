import io

from fastapi import APIRouter, Depends, File, UploadFile, Query
from fastapi.responses import StreamingResponse

from app.api import deps
from app.services.bulk_service import BulkService, BulkImportMode
from app.db import get_db_session
from app.graph.client import neo4j_dependency

router = APIRouter(prefix="/bulk", tags=["import_export"])


@router.post("/import")
async def bulk_import(
    file: UploadFile = File(...),
    format: str = Query(..., alias="format"),
    mode: str = Query(BulkImportMode.VALIDATE),
    rollback_on_error: bool = Query(True),
    session=Depends(get_db_session),
    current_user=Depends(deps.get_current_user),
    neo4j_driver=Depends(neo4j_dependency),
):
    content = await file.read()
    service = BulkService(session, lineage_driver=neo4j_driver)
    return await service.bulk_import(
        file_bytes=content,
        file_format=format,
        mode=mode,
        rollback_on_error=rollback_on_error,
    )


@router.get("/export")
async def bulk_export(
    format: str = Query(...),
    session=Depends(get_db_session),
    current_user=Depends(deps.get_current_user),
):
    service = BulkService(session)
    data = await service.bulk_export(file_format=format)
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "yaml": "application/x-yaml",
        "yml": "application/x-yaml",
        "xlsx": "application/vnd.ms-excel",
    }
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_types.get(format, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="metadata.{format}"'},
    )
