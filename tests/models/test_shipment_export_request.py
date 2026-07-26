"""Regression: ShipmentExportRequest must serialize to the portal's flat
``InternationalParams`` contract.

The ACPortal ``POST /job/{jobDisplayId}/shipment/exportdata`` body is a flat
``InternationalParams`` object (``customsValue`` required,
``additionalProperties: false``). 0.1.10 modeled ``{"exportData": dict}`` — the
real payload was rejected client-side, and the envelope shape the SDK would
send binds portal-side as all-null params, silently WIPING the job's export
data. These tests pin the flat wire shape so the destructive envelope cannot
return. GET additionally returns a per-commodity ``jobItemId`` the POST schema
forbids; the endpoint strips it to keep GET → edit → POST round-trips legal.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ab.api.endpoints.jobs.shipment import JobShipmentEndpoint
from ab.api.models.shipments import ShipmentExportRequest

FLAT_PAYLOAD = {
    "customsValue": 1500.0,
    "commodities": [
        {
            "description": "Oil painting",
            "quantity": 1,
            "unitPrice": 1500.0,
            "itemValue": 1500.0,
            "weight": 12.5,
            "countryOfManufacture": "US",
        }
    ],
    "invoiceNumber": "7435592",
    "termsOfSale": "DAP",
    "soldTo": {"contact": {"name": "Consignee"}},
    "valuesSpecified": True,
}


def test_flat_international_params_payload_is_accepted():
    wire = ShipmentExportRequest.check(FLAT_PAYLOAD)
    assert wire["customsValue"] == 1500.0
    assert wire["commodities"][0]["description"] == "Oil painting"
    assert wire["invoiceNumber"] == "7435592"
    assert wire["valuesSpecified"] is True
    # The 0.1.10 envelope must never reappear on the wire.
    assert "exportData" not in wire


def test_envelope_shape_is_rejected_client_side():
    # The exact body 0.1.10 would have sent — binds as all-null
    # InternationalParams portal-side (export-data wipe). Must not validate.
    with pytest.raises(ValidationError):
        ShipmentExportRequest.check({"exportData": FLAT_PAYLOAD})


def test_customs_value_is_required():
    incomplete = {k: v for k, v in FLAT_PAYLOAD.items() if k != "customsValue"}
    with pytest.raises(ValidationError):
        ShipmentExportRequest.check(incomplete)


def test_endpoint_strips_get_only_job_item_id_from_commodities():
    endpoint = object.__new__(JobShipmentEndpoint)
    seen = {}

    def fake_request(route, **kwargs):
        seen["json"] = kwargs["json"]
        return {"success": True}

    endpoint._request = fake_request

    round_trip = dict(FLAT_PAYLOAD)
    round_trip["commodities"] = [dict(FLAT_PAYLOAD["commodities"][0], jobItemId=987654)]
    endpoint.post_export_data(7435592, data=round_trip)

    sent = seen["json"]["commodities"][0]
    assert "jobItemId" not in sent
    assert sent["description"] == "Oil painting"
    assert seen["json"]["customsValue"] == 1500.0
