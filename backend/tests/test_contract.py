import pathlib

from schemathesis.openapi import from_path


def test_openapi_contract_loads_and_has_operations():
    spec_path = pathlib.Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.yaml"
    schema = from_path(spec_path)

    schema.validate()
    ops = list(schema.get_all_operations())
    assert ops, "No operations found in OpenAPI spec"
