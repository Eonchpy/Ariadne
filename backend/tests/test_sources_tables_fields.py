import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_sources_crud(client: AsyncClient):
    # create
    create_resp = await client.post(
        "/api/v1/sources",
        json={
            "name": "Prod Oracle",
            "type": "oracle",
            "description": "Main DB",
            "connection_config": {"host": "h", "port": 1521},
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    # list
    list_resp = await client.get("/api/v1/sources")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == created["id"]

    # get
    get_resp = await client.get(f"/api/v1/sources/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Prod Oracle"

    # update
    upd_resp = await client.put(
        f"/api/v1/sources/{created['id']}", json={"name": "Prod Oracle Updated"}
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["name"] == "Prod Oracle Updated"

    # delete
    del_resp = await client.delete(f"/api/v1/sources/{created['id']}")
    assert del_resp.status_code == 204

    # confirm deletion
    list_resp = await client.get("/api/v1/sources")
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_tables_and_fields_flow(client: AsyncClient):
    # create source prerequisite
    source_resp = await client.post(
        "/api/v1/sources",
        json={
            "name": "Source A",
            "type": "mongodb",
            "description": "Test source",
            "connection_config": {"uri": "mongodb://localhost"},
        },
    )
    source_id = source_resp.json()["id"]

    # create table
    table_resp = await client.post(
        "/api/v1/tables",
        json={
            "source_id": source_id,
            "name": "orders",
            "type": "table",
            "schema_name": "public",
            "qualified_name": "public.orders",
        },
    )
    assert table_resp.status_code == 201
    table_id = table_resp.json()["id"]

    # create field
    field_resp = await client.post(
        "/api/v1/fields",
        json={
            "table_id": table_id,
            "name": "order_id",
            "data_type": "int",
            "is_primary_key": True,
        },
    )
    assert field_resp.status_code == 201
    field_id = field_resp.json()["id"]

    # table detail includes fields
    detail_resp = await client.get(f"/api/v1/tables/{table_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["fields"]
    assert detail["fields"][0]["id"] == field_id

    # update table
    upd_resp = await client.put(f"/api/v1/tables/{table_id}", json={"description": "desc"})
    assert upd_resp.status_code == 200
    assert upd_resp.json()["description"] == "desc"

    # delete field
    del_field = await client.delete(f"/api/v1/fields/{field_id}")
    assert del_field.status_code == 204

    # delete table
    del_table = await client.delete(f"/api/v1/tables/{table_id}")
    assert del_table.status_code == 204
