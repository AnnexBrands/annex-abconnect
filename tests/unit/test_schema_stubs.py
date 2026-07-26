"""Visibility tests for schema routes that are not implemented yet."""

from __future__ import annotations

import importlib
import json
import pkgutil
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import ab.api.endpoints as endpoints_pkg
from ab.api.endpoints.account import AccountEndpoint
from ab.api.endpoints.schema_stubs import SCHEMA_STUBS
from ab.api.route import Route
from ab.cli.discovery import discover_endpoints_from_class

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "ab" / "api" / "schemas"
SCHEMA_FILES = {
    "acportal": SCHEMAS_DIR / "acportal.json",
    "abc": SCHEMAS_DIR / "abc.json",
    "catalog": SCHEMAS_DIR / "catalog.json",
}


def test_all_schema_stubs_are_discoverable_and_unrouted():
    registry = discover_endpoints_from_class()
    expected_total = sum(len(specs) for specs in SCHEMA_STUBS.values())
    discovered_total = 0

    for group, specs in SCHEMA_STUBS.items():
        assert group in registry
        methods = {method.name: method for method in registry[group].methods}
        for spec in specs:
            assert spec.method_name in methods
            assert methods[spec.method_name].route is None
            discovered_total += 1

    assert discovered_total == expected_total == 93


def test_schema_stub_registry_matches_current_route_gaps():
    implemented = _implemented_routes()
    schema_routes = _schema_routes()
    missing_routes = schema_routes - implemented
    stubbed_routes = {
        (spec.api_surface, spec.http_method, spec.path)
        for specs in SCHEMA_STUBS.values()
        for spec in specs
    }

    assert stubbed_routes == missing_routes


def test_schema_stub_raises_not_implemented_with_route_context():
    endpoint = AccountEndpoint(MagicMock(name="acportal"))

    with pytest.raises(NotImplementedError) as exc:
        endpoint.post_account_register(data={})

    assert "POST /account/register (acportal)" in str(exc.value)


def _implemented_routes() -> set[tuple[str, str, str]]:
    routes: set[tuple[str, str, str]] = set()
    for module_info in pkgutil.walk_packages(endpoints_pkg.__path__, endpoints_pkg.__name__ + "."):
        module = importlib.import_module(module_info.name)
        for name in dir(module):
            candidate = getattr(module, name, None)
            if isinstance(candidate, Route):
                routes.add((candidate.api_surface, candidate.method.upper(), candidate.path))
    return routes


def _schema_routes() -> set[tuple[str, str, str]]:
    routes: set[tuple[str, str, str]] = set()
    for surface, path in SCHEMA_FILES.items():
        spec = json.loads(path.read_text(encoding="utf-8"))
        for raw_path, operations in spec.get("paths", {}).items():
            route_path = re.sub(r"^/api(?=/)", "", raw_path)
            for method in operations:
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    routes.add((surface, method.upper(), route_path))
    return routes
