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
            elif self.source_type == SourceType.mysql:
                result = await self._test_mysql(start)
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
            import pymongo  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="pymongo not installed") from exc

        uri = self.config.get("uri")
        if not uri:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing MongoDB uri")

        def _ping():
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
            try:
                client.admin.command("ping")
            finally:
                client.close()

        try:
            await asyncio.to_thread(_ping)
        except Exception as exc:
            detail = str(exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MongoDB connection failed: {detail}",
            ) from exc
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

        username = self.config.get("username")
        password = self.config.get("password")

        def _embed_auth(h: str) -> str:
            if not username and not password:
                return h
            # if already contains scheme but no auth, inject it
            if "@" in h:
                return h
            if h.startswith("http://"):
                return f"http://{username}:{password}@{h[len('http://'):]}"
            if h.startswith("https://"):
                return f"https://{username}:{password}@{h[len('https://'):]}"
            # default to http
            return f"http://{username}:{password}@{h}"

        if isinstance(hosts, str):
            hosts_with_auth = _embed_auth(hosts)
        else:
            hosts_with_auth = [_embed_auth(h) for h in hosts]

        es_kwargs = {
            "hosts": hosts_with_auth,
            "basic_auth": (username, password) if username or password else None,
            "api_key": self.config.get("api_key"),
            "verify_certs": bool(self.config.get("use_ssl", False)),
            "ssl_show_warn": False,
        }

        es = AsyncElasticsearch(**es_kwargs)
        try:
            await es.info()
        finally:
            await es.close()
        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)

    async def _test_mysql(self, start: float) -> ConnectionTestResult:
        try:
            import aiomysql  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="aiomysql not installed") from exc

        host = self.config.get("host")
        port = int(self.config.get("port") or 3306)
        user = self.config.get("username")
        password = self.config.get("password")
        database = self.config.get("database")
        use_ssl = bool(self.config.get("use_ssl", False))

        if not host or not user or password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing MySQL connection fields (host, username, password)")

        conn = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            ssl=None if not use_ssl else {},
            connect_timeout=3,
        )
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        finally:
            conn.close()

        latency = (time.perf_counter() - start) * 1000
        return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
