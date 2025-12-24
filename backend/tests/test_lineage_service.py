import pytest
from fastapi import HTTPException

from app.services.lineage_service import LineageService


class DummyResult:
    def __init__(self, record=None):
        self._record = record or {}

    async def single(self):
        return self._record


class DummySession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def run(self, query, **params):
        self.calls.append({"query": query, "params": params})
        return DummyResult(self.responses.pop(0) if self.responses else {})


class DummyDriver:
    def __init__(self, responses):
        self.responses = responses
        self.sessions = []

    def session(self):
        session = DummySession(self.responses)
        self.sessions.append(session)
        return session

    async def close(self):
        return None


@pytest.mark.anyio
async def test_create_table_lineage_returns_rel_id():
    driver = DummyDriver(responses=[{"rel_id": 123}])
    service = LineageService(driver)
    result = await service.create_table_lineage(
        source_table_id="s1",
        target_table_id="t1",
        lineage_source="manual",
        transformation_type=None,
        transformation_logic=None,
        confidence=0.9,
    )
    assert result.id == "123"
    assert result.source_node_id == "s1"
    assert result.target_node_id == "t1"
    assert result.lineage_source == "manual"


@pytest.mark.anyio
async def test_delete_lineage_raises_when_missing():
    driver = DummyDriver(responses=[{"deleted_count": 0}])
    service = LineageService(driver)
    with pytest.raises(HTTPException) as exc:
        await service.delete_lineage(999)
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_to_graph_handles_empty_record():
    driver = DummyDriver(responses=[{}])
    service = LineageService(driver)
    graph = service._to_graph(None)
    assert graph.nodes == []
    assert graph.edges == []
    assert graph.root_id == ""
