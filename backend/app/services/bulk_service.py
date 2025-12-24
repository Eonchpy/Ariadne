import io
import json
from typing import Any

import yaml
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.table import MetadataTable
from app.models.field import MetadataField
from app.services.lineage_service import LineageService


class BulkImportMode:
    VALIDATE = "validate"
    PREVIEW = "preview"
    EXECUTE = "execute"


class BulkImportResult(dict):
    @classmethod
    def build(cls, mode: str, success: bool, summary: dict[str, Any] | None = None, errors=None, preview=None):
        return cls(
            mode=mode,
            success=success,
            summary=summary or {},
            errors=errors or [],
            preview=preview or {},
        )


class BulkService:
    SUPPORTED_FORMATS = {"csv", "json", "yaml", "yml", "xlsx"}

    def __init__(self, session: AsyncSession, lineage_driver=None):
        self.session = session
        self.lineage_driver = lineage_driver

    async def bulk_import(self, *, file_bytes: bytes, file_format: str, mode: str, rollback_on_error: bool = True) -> BulkImportResult:
        if file_format not in self.SUPPORTED_FORMATS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported format")
        if mode not in {BulkImportMode.VALIDATE, BulkImportMode.PREVIEW, BulkImportMode.EXECUTE}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported mode")

        records = self._parse(file_bytes, file_format)
        errors = await self._validate_records(records)

        summary = {
            "total_rows": len(records),
            "created": 0,
            "updated": 0,
            "skipped": len(errors),
        }

        if errors and mode == BulkImportMode.EXECUTE and rollback_on_error:
            # Do not proceed execution
            return BulkImportResult.build(mode, False, summary, errors=errors)

        preview = {"to_create": [], "to_update": []}
        # Simple deduplication check for preview: table name+source_id, field name+table_id
        existing_tables = await self._load_table_index()
        existing_fields = await self._load_field_index()

        if mode in (BulkImportMode.PREVIEW, BulkImportMode.EXECUTE):
            for rec in records:
                if rec.get("type") == "table":
                    key = (rec.get("source_id"), rec.get("name"))
                    if key in existing_tables:
                        preview["to_update"].append({"type": "table", "id": existing_tables[key], "name": rec.get("name")})
                    else:
                        preview["to_create"].append({"type": "table", "name": rec.get("name")})
                elif rec.get("type") == "field":
                    key = (rec.get("table_id"), rec.get("name"))
                    if key in existing_fields:
                        preview["to_update"].append({"type": "field", "id": existing_fields[key], "name": rec.get("name"), "table_id": rec.get("table_id")})
                    else:
                        preview["to_create"].append({"type": "field", "name": rec.get("name"), "table_id": rec.get("table_id")})
                elif rec.get("type") in {"table_lineage", "field_lineage"}:
                    preview["to_create"].append(rec)

        if mode == BulkImportMode.EXECUTE and not errors:
            async with self.session.begin():
                for rec in records:
                    if rec.get("type") == "table":
                        table = MetadataTable(
                            name=rec.get("name"),
                            schema_name=rec.get("schema_name"),
                            qualified_name=rec.get("qualified_name"),
                            source_id=rec.get("source_id"),
                            description=rec.get("description"),
                        )
                        self.session.add(table)
                        summary["created"] += 1
                    elif rec.get("type") == "field":
                        field = MetadataField(
                            table_id=rec.get("table_id"),
                            name=rec.get("name"),
                            data_type=rec.get("data_type"),
                            description=rec.get("description"),
                            is_nullable=rec.get("is_nullable"),
                            is_primary_key=rec.get("is_primary_key"),
                            is_foreign_key=rec.get("is_foreign_key"),
                        )
                        self.session.add(field)
                        summary["created"] += 1
                # Commit transaction block by exiting context

            # Process lineage outside DB transaction, against Neo4j if configured
            lineage_records = [r for r in records if r.get("type") in {"table_lineage", "field_lineage"}]
            if lineage_records:
                if not self.lineage_driver:
                    errors.append({"row": None, "entity": "lineage", "message": "Neo4j driver not available", "code": "NO_NEO4J"})
                else:
                    service = LineageService(self.lineage_driver)
                    for rec in lineage_records:
                        if rec.get("type") == "table_lineage":
                            await service.create_table_lineage(
                                source_table_id=rec.get("source_table_id"),
                                target_table_id=rec.get("target_table_id"),
                                lineage_source=rec.get("lineage_source", "manual"),
                                transformation_type=rec.get("transformation_type"),
                                transformation_logic=rec.get("transformation_logic"),
                                confidence=rec.get("confidence"),
                            )
                            summary["created"] += 1
                        elif rec.get("type") == "field_lineage":
                            await service.create_field_lineage(
                                source_field_id=rec.get("source_field_id"),
                                target_field_id=rec.get("target_field_id"),
                                lineage_source=rec.get("lineage_source", "manual"),
                                transformation_logic=rec.get("transformation_logic"),
                                confidence=rec.get("confidence"),
                            )
                            summary["created"] += 1

        success = len(errors) == 0
        return BulkImportResult.build(mode, success, summary, errors=errors, preview=preview if mode == BulkImportMode.PREVIEW else {})

    async def _validate_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        table_ids = set()
        field_ids = set()
        for idx, rec in enumerate(records, start=1):
            if "type" not in rec:
                errors.append({"row": idx, "entity": "unknown", "message": "Missing type", "code": "MISSING_TYPE"})
                continue
            rtype = rec["type"]
            if rtype == "table":
                if "name" not in rec:
                    errors.append({"row": idx, "entity": "table", "message": "Missing table name", "code": "MISSING_NAME"})
                if "source_id" not in rec:
                    errors.append({"row": idx, "entity": "table", "message": "Missing source_id", "code": "MISSING_SOURCE"})
            elif rtype == "field":
                if "table_id" not in rec:
                    errors.append({"row": idx, "entity": "field", "message": "Missing table_id", "code": "MISSING_TABLE_ID"})
                if "name" not in rec or "data_type" not in rec:
                    errors.append({"row": idx, "entity": "field", "message": "Missing name or data_type", "code": "MISSING_REQUIRED"})
                if "table_id" in rec:
                    table_ids.add(rec["table_id"])
            elif rtype == "table_lineage":
                if not rec.get("source_table_id") or not rec.get("target_table_id"):
                    errors.append({"row": idx, "entity": "table_lineage", "message": "Missing source_table_id or target_table_id", "code": "MISSING_REQUIRED"})
                else:
                    table_ids.update([rec["source_table_id"], rec["target_table_id"]])
            elif rtype == "field_lineage":
                if not rec.get("source_field_id") or not rec.get("target_field_id"):
                    errors.append({"row": idx, "entity": "field_lineage", "message": "Missing source_field_id or target_field_id", "code": "MISSING_REQUIRED"})
                else:
                    field_ids.update([rec["source_field_id"], rec["target_field_id"]])

        # Referential checks for tables/fields
        missing_tables = await self._missing_ids(MetadataTable, table_ids)
        for t in missing_tables:
            errors.append({"row": None, "entity": "table", "message": f"Referenced table_id not found: {t}", "code": "MISSING_REF"})
        missing_fields = await self._missing_ids(MetadataField, field_ids)
        for f in missing_fields:
            errors.append({"row": None, "entity": "field", "message": f"Referenced field_id not found: {f}", "code": "MISSING_REF"})
        return errors

    async def _missing_ids(self, model, ids: set) -> list[str]:
        if not ids:
            return []
        result = await self.session.execute(select(model.id).where(model.id.in_(list(ids))))
        found = {str(r[0]) for r in result.fetchall()}
        return [str(i) for i in ids if str(i) not in found]

    async def _load_table_index(self) -> dict[tuple[str | None, str | None], str]:
        result = await self.session.execute(select(MetadataTable.id, MetadataTable.source_id, MetadataTable.name))
        return {(str(r.source_id) if r.source_id else None, r.name): str(r.id) for r in result.fetchall()}

    async def _load_field_index(self) -> dict[tuple[str | None, str | None], str]:
        result = await self.session.execute(select(MetadataField.id, MetadataField.table_id, MetadataField.name))
        return {(str(r.table_id) if r.table_id else None, r.name): str(r.id) for r in result.fetchall()}

    def _parse(self, file_bytes: bytes, file_format: str) -> list[dict[str, Any]]:
        fmt = file_format.lower()
        if fmt == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
            return df.to_dict(orient="records")
        if fmt in {"yaml", "yml"}:
            return yaml.safe_load(io.BytesIO(file_bytes)) or []
        if fmt == "json":
            return json.loads(file_bytes.decode("utf-8"))
        if fmt == "xlsx":
            df = pd.read_excel(io.BytesIO(file_bytes))
            return df.to_dict(orient="records")
        return []

    async def bulk_export(self, *, file_format: str) -> bytes:
        if file_format not in self.SUPPORTED_FORMATS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported format")

        # Minimal placeholder export: export tables only
        rows = []
        result = await self.session.execute(MetadataTable.__table__.select())
        for row in result.fetchall():
            rows.append(dict(row._mapping))

        buf = io.BytesIO()
        fmt = file_format.lower()
        if fmt == "csv":
            pd.DataFrame(rows).to_csv(buf, index=False)
            return buf.getvalue()
        if fmt == "json":
            return json.dumps(rows).encode("utf-8")
        if fmt in {"yaml", "yml"}:
            return yaml.safe_dump(rows).encode("utf-8")
        if fmt == "xlsx":
            pd.DataFrame(rows).to_excel(buf, index=False)
            return buf.getvalue()
        return b""
