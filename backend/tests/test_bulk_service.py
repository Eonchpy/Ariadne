import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.bulk_service import BulkService, BulkImportMode
from app.db import get_db_session
from app.main import app
from httpx import AsyncClient, ASGITransport


@pytest.mark.anyio
async def test_bulk_import_validate_mode(db_session: AsyncSession):
    service = BulkService(db_session)
    data = b"type,name,source_id\n" + b"table,users,00000000-0000-0000-0000-000000000000\n"
    result = await service.bulk_import(file_bytes=data, file_format="csv", mode=BulkImportMode.VALIDATE)
    assert result["mode"] == "validate"
    assert result["success"] is True
    assert result["summary"]["total_rows"] == 1


@pytest.mark.anyio
async def test_bulk_import_errors_on_missing_type(db_session: AsyncSession):
    service = BulkService(db_session)
    data = b"name\n" + b"no_type_row\n"
    result = await service.bulk_import(file_bytes=data, file_format="csv", mode=BulkImportMode.VALIDATE)
    assert result["success"] is False
    assert result["errors"]


@pytest.mark.anyio
async def test_bulk_export_json(db_session: AsyncSession):
    service = BulkService(db_session)
    payload = await service.bulk_export(file_format="json")
    assert isinstance(payload, (bytes, bytearray))


@pytest.mark.anyio
async def test_bulk_import_field_ref_missing_table(db_session: AsyncSession):
    service = BulkService(db_session)
    records = [
        {"type": "field", "table_id": "11111111-1111-1111-1111-111111111111", "name": "col", "data_type": "text"}
    ]
    data = "\n".join(["type,table_id,name,data_type", "field,11111111-1111-1111-1111-111111111111,col,text"]).encode()
    result = await service.bulk_import(file_bytes=data, file_format="csv", mode=BulkImportMode.VALIDATE)
    assert result["success"] is False
    assert any(err["code"] == "MISSING_REF" for err in result["errors"])
