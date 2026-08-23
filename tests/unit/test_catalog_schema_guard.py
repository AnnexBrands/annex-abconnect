"""The catalog surface is guarded against the environment it does not model.

The migrated Catalog schema (``agentCompanyIds``, a singular ``seller``,
per-platform external IDs, ``/Platform``, ``/Bulk/upsert``) is deployed to
staging only; production still serves the pre-migration schema. Calling the
catalog surface against production must fail with an explanation rather than
sending a body the old API rejects or silently dropping fields it returns.
"""

from __future__ import annotations

import pytest

from ab.api.endpoints.catalog import CatalogEndpoint
from ab.api.endpoints.lots import LotsEndpoint
from ab.api.endpoints.platforms import PlatformsEndpoint
from ab.api.endpoints.sellers import SellersEndpoint
from ab.exceptions import CatalogSchemaMismatchError


class _StubClient:
    """Minimal HttpClient stand-in that records whether a call went out."""

    def __init__(self, environment: str | None) -> None:
        if environment is not None:
            self.environment = environment
        self.calls: list[tuple[str, str]] = []

    #: Superset payload that satisfies every model on the catalog surface, so
    #: the unguarded cases exercise the guard rather than response validation.
    RESPONSE = {
        "id": 1,
        "lotId": 1,
        "startDate": "2026-01-01T00:00:00Z",
        "endDate": "2026-01-02T00:00:00Z",
        "isCompleted": False,
        "partnerId": 77,
        "isActive": True,
        "customerDisplayId": 1,
        "items": [],
    }

    def request(self, method, path, **kwargs):
        self.calls.append((method, path))
        return dict(self.RESPONSE)


def _endpoints(environment):
    client = _StubClient(environment)
    return client, [
        ("catalog.get", lambda: CatalogEndpoint(client).get(1)),
        ("catalog.list", lambda: CatalogEndpoint(client).list()),
        ("catalog.merge", lambda: CatalogEndpoint(client).merge(1, 2)),
        ("catalog.bulk_upsert", lambda: CatalogEndpoint(client).bulk_upsert(data={"catalogs": []})),
        ("lots.get", lambda: LotsEndpoint(client).get(1)),
        ("lots.list", lambda: LotsEndpoint(client).list()),
        ("lots.list_client_item_data", lambda: LotsEndpoint(client).list_client_item_data(1)),
        ("sellers.get", lambda: SellersEndpoint(client).get(1)),
        ("platforms.list", lambda: PlatformsEndpoint(client).list()),
        ("platforms.get", lambda: PlatformsEndpoint(client).get(1)),
    ]


def test_production_calls_raise_before_any_request_goes_out():
    client, cases = _endpoints("production")
    for name, call in cases:
        with pytest.raises(CatalogSchemaMismatchError):
            call()
    assert client.calls == [], f"guard let requests through: {client.calls}"


def test_error_names_the_environment_and_the_route():
    client = _StubClient("production")
    with pytest.raises(CatalogSchemaMismatchError) as exc:
        CatalogEndpoint(client).get(1)
    message = str(exc.value)
    assert "'production'" in message
    assert "/Catalog/1" in message
    assert "staging" in message


def test_staging_calls_are_not_guarded():
    client, cases = _endpoints("staging")
    for _name, call in cases:
        call()
    assert len(client.calls) == len(cases)


def test_client_without_environment_is_not_guarded():
    """Test doubles that expose no ``environment`` must keep working."""
    client, cases = _endpoints(None)
    for _name, call in cases:
        call()
    assert len(client.calls) == len(cases)


def test_non_catalog_surfaces_are_unaffected():
    from ab.api.endpoints.account import AccountEndpoint

    client = _StubClient("production")
    AccountEndpoint(client).get_profile()
    assert client.calls, "acportal surface must not be guarded"
