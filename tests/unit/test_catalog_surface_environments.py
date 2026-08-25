"""The catalog surface is not environment-guarded.

0.2.0 and 0.2.1 refused catalog-surface calls against production with
``CatalogSchemaMismatchError``, because the migrated Catalog schema was
deployed to staging only. 0.2.2 completes the cutover: the SDK models the
migrated schema unconditionally and environment skew is handled by pinning
(the sole consumer pins 0.2.1 for production until its Catalog API migrates),
not by a runtime guard.

These tests keep the guard from coming back by accident.
"""

from __future__ import annotations

import ab.exceptions
from ab.api.endpoints.catalog import CatalogEndpoint
from ab.api.endpoints.lots import LotsEndpoint
from ab.api.endpoints.platforms import PlatformsEndpoint
from ab.api.endpoints.sellers import SellersEndpoint


class _StubClient:
    """Minimal HttpClient stand-in that records whether a call went out."""

    def __init__(self, environment: str | None) -> None:
        if environment is not None:
            self.environment = environment
        self.calls: list[tuple[str, str]] = []

    #: Superset payload that satisfies every model on the catalog surface, so
    #: the cases exercise routing rather than response validation.
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


def test_production_calls_go_out_unguarded():
    client, cases = _endpoints("production")
    for _name, call in cases:
        call()
    assert len(client.calls) == len(cases)


def test_staging_calls_go_out_unguarded():
    client, cases = _endpoints("staging")
    for _name, call in cases:
        call()
    assert len(client.calls) == len(cases)


def test_client_without_environment_is_unguarded():
    """Test doubles that expose no ``environment`` must keep working."""
    client, cases = _endpoints(None)
    for _name, call in cases:
        call()
    assert len(client.calls) == len(cases)


def test_catalog_schema_mismatch_error_is_gone():
    """The exception was the guard's only reason to exist — it must not linger
    as dead API surface that callers could still try to catch."""
    assert not hasattr(ab.exceptions, "CatalogSchemaMismatchError")
