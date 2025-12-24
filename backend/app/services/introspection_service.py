import asyncio
from typing import Any

from fastapi import HTTPException, status

from app.schemas.table import TableDetail
from app.schemas.field import Field
from app.schemas.source import SourceType
from app.core.encryption import decrypt_dict
from app.services.connection_service import _ensure_oracle_thick_client


class IntrospectionService:
    def __init__(self, source_type: SourceType, connection_config: dict[str, Any]):
        self.source_type = source_type
        self.config = decrypt_dict(connection_config or {})
        # Normalize Oracle EZ Connect if provided as host/port/service_name
        if self.source_type == SourceType.oracle:
            _ensure_oracle_thick_client()
            host = self.config.get("host")
            service = self.config.get("service_name")
            port = self.config.get("port") or 1521
            if not self.config.get("dsn") and host and service:
                self.config["dsn"] = f"{host}:{port}/{service}"

    async def introspect_table(self, table_name: str, schema_name: str | None = None) -> TableDetail:
        if self.source_type == SourceType.oracle:
            return await self._oracle_table(table_name, schema_name)
        if self.source_type == SourceType.mongodb:
            return await self._mongodb_collection(table_name)
        if self.source_type == SourceType.elasticsearch:
            return await self._elasticsearch_index(table_name)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source type")

    async def _oracle_table(self, table_name: str, schema_name: str | None) -> TableDetail:
        try:
            import oracledb  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="oracledb not installed") from exc

        user = self.config.get("username")
        password = self.config.get("password")
        dsn = self.config.get("dsn")
        if not user or not password or not dsn:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Oracle connection fields")

        # Note: Using synchronous oracle client calls inside async; wrap in thread to avoid blocking event loop.
        async def _fetch():
            def _sync_fetch():
                with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
                    cur = conn.cursor()
                    owner_filter = schema_name or user.upper()
                    cur.execute(
                        """
                        SELECT column_name, data_type, nullable, data_precision, data_scale
                        FROM all_tab_columns
                        WHERE owner=:owner_name AND table_name=:table_name
                        ORDER BY column_id
                        """,
                        owner_name=owner_filter.upper(),
                        table_name=table_name.upper(),
                    )
                    cols = cur.fetchall()

                    cur.execute(
                        """
                        SELECT acc.column_name
                        FROM all_constraints ac
                        JOIN all_cons_columns acc ON ac.constraint_name = acc.constraint_name
                        WHERE ac.owner=:owner_name AND ac.table_name=:table_name AND ac.constraint_type='P'
                        """,
                        owner_name=owner_filter.upper(),
                        table_name=table_name.upper(),
                    )
                    pk_cols = {row[0] for row in cur.fetchall()}

                    return cols, pk_cols

            return await asyncio.to_thread(_sync_fetch)

        cols, pk_cols = await _fetch()
        fields = []
        for col in cols:
            name, data_type, nullable, precision, scale = col
            fields.append(
                Field(
                    id="",
                    table_id="",
                    name=name,
                    data_type=f"{data_type}({precision},{scale})" if precision else data_type,
                    is_nullable=nullable == "Y",
                    is_primary_key=name in pk_cols,
                )
            )

        return TableDetail(
            id="",
            source_id="",
            name=table_name,
            schema_name=schema_name,
            qualified_name=f"{schema_name}.{table_name}" if schema_name else table_name,
            fields=fields,
        )

    async def _mongodb_collection(self, collection_name: str) -> TableDetail:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="pymongo/motor not installed") from exc

        uri = self.config.get("uri")
        db_name = self.config.get("database")
        if not uri or not db_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Mongo uri or database")

        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]
        coll = db[collection_name]
        # Sample one document to infer fields
        doc = await coll.find_one()
        client.close()

        fields = []
        if doc:
            for key, value in doc.items():
                dtype = type(value).__name__
                fields.append(
                    Field(
                        id="",
                        table_id="",
                        name=key,
                        data_type=dtype,
                        is_nullable=True,
                        is_primary_key=key == "_id",
                    )
                )

        return TableDetail(
            id="",
            source_id="",
            name=collection_name,
            schema_name=db_name,
            qualified_name=f"{db_name}.{collection_name}",
            fields=fields,
        )

    async def _elasticsearch_index(self, index_name: str) -> TableDetail:
        try:
            from elasticsearch import AsyncElasticsearch  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="elasticsearch client not installed") from exc

        hosts = self.config.get("hosts") or self.config.get("host")
        if not hosts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Elasticsearch hosts")

        es = AsyncElasticsearch(hosts=hosts)
        try:
            mapping = await es.indices.get_mapping(index=index_name)
        finally:
            await es.close()

        fields = []
        if index_name in mapping:
            props = mapping[index_name]["mappings"].get("properties", {})
            for key, value in props.items():
                dtype = value.get("type", "object")
                fields.append(
                    Field(
                        id="",
                        table_id="",
                        name=key,
                        data_type=dtype,
                        is_nullable=True,
                        is_primary_key=False,
                    )
                )

        return TableDetail(
            id="",
            source_id="",
            name=index_name,
            schema_name=None,
            qualified_name=index_name,
            fields=fields,
        )
