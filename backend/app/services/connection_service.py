import asyncio
import time
from typing import Any

from fastapi import HTTPException, status

from app.schemas.source import ConnectionTestResult, SourceType
from app.core.encryption import decrypt_dict
from app.repositories.audit_repo import ConnectionTestLogRepository
from app.models.audit import ConnectionTestLog
from app.repositories.source_repo import SourceRepository
from app.config import settings

_oracle_client_initialized = False


def _ensure_oracle_thick_client():
    """Initialize Oracle thick client if lib dir is configured and not already initialized."""
    global _oracle_client_initialized
    if _oracle_client_initialized:
        return
    try:
        import oracledb  # type: ignore
    except ImportError:
        return  # not installed; let caller handle
    if not getattr(oracledb, "is_thin_mode", None):
        return
    if not oracledb.is_thin_mode():
        _oracle_client_initialized = True
        return
    lib_dir = settings.ORACLE_CLIENT_LIB_DIR
    if not lib_dir:
        return
    try:
        oracledb.init_oracle_client(lib_dir=lib_dir)  # type: ignore[attr-defined]
        _oracle_client_initialized = True
    except Exception:
        # swallow init errors; connect will raise informative error later
        return


class ConnectionService:
    def __init__(self, source_type: SourceType, connection_config: dict[str, Any], audit_repo: ConnectionTestLogRepository | None = None):
        self.source_type = source_type
        self.config = decrypt_dict(connection_config or {})
        self.audit_repo = audit_repo

    async def test_connection(self, source_id: str | None = None, tested_by: str | None = None) -> ConnectionTestResult:
        start = time.perf_counter()
        try:
            if self.source_type == SourceType.oracle:
                result = await self._test_oracle(start)
            elif self.source_type == SourceType.mongodb:
                result = await self._test_mongodb(start)
            elif self.source_type == SourceType.elasticsearch:
                result = await self._test_elasticsearch(start)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source type")
            await self._log(source_id, "connection_test", tested_by, "success", None, table_name=None)
            return result
        except Exception as exc:
            await self._log(source_id, "connection_test", tested_by, "failure", str(exc), table_name=None)
            raise

    async def _test_oracle(self, start: float) -> ConnectionTestResult:
        try:
            import oracledb  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="oracledb not installed") from exc

        # Build EZ Connect if host/port/service_name provided; otherwise use provided dsn
        user = self.config.get("username")
        password = self.config.get("password")
        host = self.config.get("host")
        service_name = self.config.get("service_name")
        port = self.config.get("port") or 1521
        dsn = self.config.get("dsn")
        if not dsn and host and service_name:
            dsn = f"{host}:{port}/{service_name}"
        if not dsn or not user or not password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Oracle connection fields (dsn or host/service_name, username, password)")

        _ensure_oracle_thick_client()
        # Let driver errors surface; run sync connect in a thread to avoid blocking loop
        def _connect_sync():
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            conn.close()

        await asyncio.to_thread(_connect_sync)
        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)

    async def _log(
        self,
        source_id: str | None,
        operation: str,
        tested_by: str | None,
        result: str,
        error_message: str | None,
        table_name: str | None,
    ) -> None:
        if not self.audit_repo:
            return
        log = ConnectionTestLog(
            source_id=source_id,
            operation=operation,
            tested_by=tested_by,
            result=result,
            error_message=error_message,
            table_name=table_name,
        )
        await self.audit_repo.add(log)
        await self.audit_repo.session.commit()

    async def _test_mongodb(self, start: float) -> ConnectionTestResult:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="pymongo/motor not installed") from exc

        uri = self.config.get("uri")
        if not uri:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing MongoDB uri")

        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000)
        try:
            await client.admin.command("ping")
        finally:
            client.close()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)

    async def _test_elasticsearch(self, start: float) -> ConnectionTestResult:
        try:
            from elasticsearch import AsyncElasticsearch  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="elasticsearch client not installed") from exc

        hosts = self.config.get("hosts") or self.config.get("host")
        if not hosts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Elasticsearch hosts")

        es = AsyncElasticsearch(hosts=hosts)
        try:
            await es.info()
        finally:
            await es.close()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
