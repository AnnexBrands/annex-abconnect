"""8_01 migrations fail before I/O, and current contracts preserve selectors."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from pydantic import ValidationError

from ab.api.base import BaseEndpoint
from ab.api.endpoints.companies import CompaniesEndpoint
from ab.api.endpoints.jobs import JobFreightProvidersEndpoint, JobsEndpoint, JobShipmentEndpoint
from ab.api.endpoints.shipments import ShipmentsEndpoint
from ab.api.helpers.items import JobItemsHelpers
from ab.api.models.release_support import CommonInventoryRequest, SaveFinalQuoteRequest
from ab.cli.discovery import discover_endpoints_from_class
from ab.exceptions import UnsupportedOperationError


def removed_methods():
    return [
        (group, m.name, info.endpoint_class, m.route)
        for group, info in discover_endpoints_from_class().items()
        for m in info.methods
        if m.route and m.route.unsupported_reason
    ]


@pytest.mark.parametrize("group,name,cls,route", removed_methods(), ids=lambda x: x if isinstance(x, str) else None)
def test_removed_contracts_fail_before_transport(group, name, cls, route):
    client = MagicMock()
    endpoint = object.__new__(cls)
    BaseEndpoint.__init__(endpoint, client)
    call = getattr(endpoint, name)
    kwargs = {
        n: ({} if n == "data" else 123)
        for n, p in inspect.signature(call).parameters.items()
        if p.default is inspect.Parameter.empty and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)
    }
    with pytest.raises(UnsupportedOperationError, match="8_01|implement"):
        call(**kwargs)
    client.request.assert_not_called()
    assert route.bind(jobDisplayId=123).unsupported_reason == route.unsupported_reason


@pytest.mark.parametrize(
    "name,args,kwargs",
    [
        ("upsert_parcel", (1,), {"description": "Box", "unknown": 1}),
        ("update_parcel", (1, "legacy-id"), {"weight": 3}),
        ("delete_parcel", (1, "legacy-id"), {}),
        ("replace_parcel", (1, "legacy-id"), {"description": "Box"}),
        ("set_freight", (1, []), {}),
        ("upsert_freight", (1,), {"weight": 5}),
        ("replace_freight", (1, "legacy-id"), {}),
        ("delete_freight", (1, "legacy-id"), {}),
    ],
)
def test_item_helpers_reject_lossy_mapping_before_reads_or_writes(name, args, kwargs):
    jobs = MagicMock()
    with pytest.raises(UnsupportedOperationError, match="inventory.*handling_units"):
        getattr(JobItemsHelpers(jobs), name)(*args, **kwargs)
    assert jobs.mock_calls == []


@pytest.mark.parametrize("name", ["get_rate_quotes_result", "request_rate_quotes_result"])
def test_raw_rate_helpers_do_not_bypass_guards(name):
    client = MagicMock()
    with pytest.raises(UnsupportedOperationError, match="rates.request"):
        getattr(JobShipmentEndpoint(client), name)(1, **({"data": {}} if name.startswith("request") else {}))
    client.request.assert_not_called()


def test_old_inventory_uuid_and_old_provider_view_require_explicit_migration():
    client = MagicMock()
    with pytest.raises(UnsupportedOperationError, match="integer"):
        JobsEndpoint(client, client, MagicMock()).update_item(1, "legacy-uuid", data={})
    with pytest.raises(UnsupportedOperationError, match="get_quotes"):
        JobFreightProvidersEndpoint(client).list(1)
    client.request.assert_not_called()


def test_current_freight_filters_use_exact_server_aliases():
    client = MagicMock()
    client.request.return_value = []
    JobFreightProvidersEndpoint(client).get_quotes(123, active=False, is_overridden=True, shipped=False)
    client.request.assert_called_once_with(
        "GET", "/job/123/freightproviders", params={"Active": False, "IsOverridden": True, "Shipped": False}
    )


def test_final_quote_rejects_unknown_nested_fields_without_dropping_concurrency():
    with pytest.raises(ValidationError):
        SaveFinalQuoteRequest.model_validate({"quote": {"id": str(UUID(int=1)), "oldOptionIndex": 6}})
    payload = SaveFinalQuoteRequest.check(
        {
            "quote": {"id": str(UUID(int=1)), "shippingId": 12},
            "jobModifiedDate": "2026-10-11T00:00:00Z",
            "forceUpdate": False,
        }
    )
    assert payload["quote"]["shippingId"] == 12
    assert payload["forceUpdate"] is False and payload["jobModifiedDate"]


def test_company_inventory_validates_constraints_and_explicit_null():
    with pytest.raises(ValidationError):
        CommonInventoryRequest.model_validate({"isActive": True, "isPublic": False, "length": 1001})
    client = MagicMock()
    client.request.return_value = None
    CompaniesEndpoint(client, MagicMock()).update_inventory(
        str(UUID(int=1)), 2, data={"isActive": True, "isPublic": False, "parentInventoryItemId": None}
    )
    assert client.request.call_args.kwargs["json"]["parentInventoryItemId"] is None


def test_shipment_document_requires_franchisee_and_uses_query():
    client = MagicMock()
    client.request.return_value = None
    endpoint = ShipmentsEndpoint(client)
    with pytest.raises(ValueError, match="franchisee_id"):
        endpoint.get_shipment_document("doc")
    client.request.assert_not_called()
    endpoint.get_shipment_document("doc", franchisee_id=str(UUID(int=1)))
    client.request.assert_called_once_with(
        "GET", "/shipment/document", params={"DocId": "doc", "FranchiseeId": str(UUID(int=1))}
    )
