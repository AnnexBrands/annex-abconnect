"""8_01 transport and selector tests using synthetic data, never live bookings."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ab.api.endpoints.jobs.rates import JobRatesEndpoint
from ab.api.endpoints.jobs.shipment import JobShipmentEndpoint
from ab.api.models.transportation import ShippingExportData

QUOTE = "11111111-2222-4333-8444-555555555555"


@pytest.mark.parametrize("method,path", [("book_v2", "v2/book"), ("validate", "validate")])
def test_quote_booking_preserves_concurrency_and_carrier_result(method, path):
    client = MagicMock()
    client.request.return_value = (
        {"success": True, "shipmentId": "carrier-id"} if method == "book_v2" else {"valid": True}
    )
    result = getattr(JobShipmentEndpoint(client), method)(
        123,
        quote_id=QUOTE,
        job_modified_date="2026-10-11T01:02:03Z",
        ship_out_date="2026-10-12T00:00:00Z",
    )
    client.request.assert_called_once_with(
        "POST",
        f"/job/123/shipment/{path}",
        json={
            "quoteId": QUOTE,
            "jobModifiedDate": "2026-10-11T01:02:03Z",
            "shipOutDate": "2026-10-12T00:00:00Z",
        },
    )
    if method == "book_v2":
        assert result.shipment_id == "carrier-id"
    else:
        assert result.valid


@pytest.mark.parametrize("quote", [None, 123, "carrier-id", "00000000-0000-0000-0000-000000000000"])
@pytest.mark.parametrize("method", ["book_v2", "validate", "cancel"])
def test_invalid_quote_selector_never_reaches_http(quote, method):
    client = MagicMock()
    with pytest.raises((ValueError, ValidationError)):
        getattr(JobShipmentEndpoint(client), method)(123, quote_id=quote)
    client.request.assert_not_called()


def test_cancel_binds_quote_not_shipping_id_and_sends_concurrency():
    client = MagicMock()
    client.request.return_value = {"success": True, "overrideError": False}
    result = JobShipmentEndpoint(client).cancel(123, QUOTE, force_delete=False, force_update=False)
    assert result.success
    client.request.assert_called_once_with(
        "PUT",
        f"/job/123/shipment/cancel/{QUOTE}",
        json={"forceDelete": False, "forceUpdate": False},
    )


@pytest.mark.parametrize("value", [QUOTE, 0, -1, True, None])
def test_invalid_shipping_selector_never_reaches_http(value):
    client = MagicMock()
    with pytest.raises(ValueError):
        JobShipmentEndpoint(client).save_shipping_export_data(123, value, customs_value=10)
    client.request.assert_not_called()


def test_export_round_trip_retains_commodity_ids_and_explicit_nulls():
    client = MagicMock()
    client.request.return_value = None
    # Synthetic server-shaped response, not a captured fixture.
    result = ShippingExportData.model_validate(
        {
            "customsValue": 10,
            "invoiceNumber": None,
            "commodities": [{"jobItemId": QUOTE, "quantity": 1, "weight": 2, "unitPrice": 10}],
        }
    )
    body = result.model_dump(mode="json", by_alias=True, exclude_unset=True)
    JobShipmentEndpoint(client).save_shipping_export_data(123, 17, **body)
    client.request.assert_called_once_with("POST", "/job/123/shipment/exportdata/17", json=body)


def test_unknown_nested_export_field_fails_before_http():
    client = MagicMock()
    with pytest.raises(ValidationError):
        JobShipmentEndpoint(client).book_v2(
            123, quote_id=QUOTE, international_params={"customsValue": 10, "typo": True}
        )
    client.request.assert_not_called()


def test_rates_preserve_handling_unit_identity_and_quote_selection():
    client = MagicMock()
    client.request.return_value = {"ratesKey": "synthetic-key", "providers": [], "warnings": [], "errors": []}
    rates = JobRatesEndpoint(client).request(
        123,
        handling_units=[{"id": 20, "quantity": 2, "weight": 50}],
        origin_address={"zipCode": "90210"},
        destination_address={"zipCode": "10001"},
    )
    assert rates.rates_key == "synthetic-key"
    assert client.request.call_args.kwargs["json"]["handlingUnits"][0]["id"] == 20
    client.reset_mock()
    client.request.return_value = {"success": True, "transportationQuote": {"id": QUOTE, "shippingId": 17}}
    result = JobRatesEndpoint(client).select_quote(123, rates_key=rates.rates_key, carrier_code="synthetic-carrier")
    assert str(result.transportation_quote.id) == QUOTE
    assert result.transportation_quote.shipping_id == 17
    client.request.assert_called_once_with(
        "POST",
        "/job/123/rates/select-quote",
        json={"ratesKey": "synthetic-key", "carrierCode": "synthetic-carrier"},
    )


def test_rate_request_rejects_empty_handling_unit_collection():
    client = MagicMock()
    with pytest.raises(ValidationError):
        JobRatesEndpoint(client).request(
            123,
            handling_units=[],
            origin_address={"zipCode": "90210"},
            destination_address={"zipCode": "10001"},
        )
    client.request.assert_not_called()


def test_export_edit_helper_removes_only_computed_description():
    result = ShippingExportData.model_validate(
        {
            "customsValue": 10,
            "commodities": [
                {"quantity": 1, "unitPrice": 10, "weight": 2, "jobItemId": QUOTE, "fullDescription": "computed"}
            ],
        }
    )
    payload = result.to_request().check(result.to_request())
    assert payload["commodities"][0]["jobItemId"] == QUOTE
    assert "fullDescription" not in payload["commodities"][0]
    result.model_extra["unknownFutureField"] = 1
    with pytest.raises(ValidationError):
        result.to_request()
