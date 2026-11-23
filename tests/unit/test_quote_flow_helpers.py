"""8_01 quote flow: typed stale-job error, one-write override, mark_selected, quote state helpers."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from ab.api.endpoints.jobs.freight_providers import JobFreightProvidersEndpoint, NewFinalOverride
from ab.api.models.release_support import TransportationQuoteResult
from ab.api.selection import is_carrier_booked, is_recorded_override, is_untouched_estimate
from ab.exceptions import JobModifiedConflictError, RequestError
from ab.http import HttpClient

PARCEL = "778a28ef-4866-4878-a87a-9fa6333a48a6"


def _response(status, payload):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    resp.text = str(payload)
    resp.url = "https://host.example/api/job/1/freightproviders/final"
    resp.request.method = "POST"
    return resp


def test_stale_job_stamp_is_a_typed_error():
    body = {
        "refreshRequired": True,
        "message": "This job was already updated by A User. Refresh page to get the latest changes?",
        "modifiedBy": "A User",
        "modifiedBySystem": False,
    }
    with pytest.raises(JobModifiedConflictError) as caught:
        HttpClient._handle_response(_response(400, body))
    error = caught.value
    assert isinstance(error, RequestError)
    assert error.status_code == 400
    assert error.refresh_required and not error.force_update_required
    assert error.modified_by == "A User" and error.modified_by_system is False
    assert "already updated" in error.message


def test_force_update_conflict_is_typed_too():
    with pytest.raises(JobModifiedConflictError) as caught:
        HttpClient._handle_response(_response(400, {"forceUpdateRequired": True, "message": "m"}))
    assert caught.value.force_update_required and not caught.value.refresh_required


def test_other_400s_stay_plain_request_errors():
    with pytest.raises(RequestError) as caught:
        HttpClient._handle_response(_response(400, {"message": "Job ID is required."}))
    assert type(caught.value) is RequestError


def _endpoint():
    endpoint = JobFreightProvidersEndpoint.__new__(JobFreightProvidersEndpoint)
    endpoint.save_final_quote = MagicMock(return_value=SimpleNamespace(success=True))
    return endpoint


def test_save_new_final_override_posts_a_complete_override_under_a_new_id():
    endpoint = _endpoint()
    provider = uuid4()
    result = endpoint.save_new_final_override(
        7,
        shipping_id=11,
        shipment_type=PARCEL,
        provider_id=provider,
        provider_company_name="Direct UPS",
        freight_amount=12.5,
        job_modified_date="2026-11-23T00:00:00Z",
    )
    assert isinstance(result, NewFinalOverride)
    (job,), kwargs = endpoint.save_final_quote.call_args
    data = kwargs["data"]
    assert job == 7
    assert data["jobModifiedDate"] == "2026-11-23T00:00:00Z"
    assert "handlingUnits" not in data
    quote = data["quote"]
    assert UUID(quote["id"]) == result.quote_id
    assert quote == {
        "id": str(result.quote_id),
        "isOverridden": True,
        "active": True,
        "shippingId": 11,
        "shipmentType": PARCEL,
        "providerId": str(provider),
        "providerCompanyName": "Direct UPS",
        "freightAmount": 12.5,
        "accessorialAmount": 0.0,
    }


def test_save_new_final_override_passes_optional_fields_and_units():
    endpoint = _endpoint()
    endpoint.save_new_final_override(
        7,
        shipping_id=11,
        shipment_type=PARCEL,
        provider_id=uuid4(),
        provider_company_name="Direct",
        freight_amount=1,
        accessorial_amount=2,
        provider_code="UPS03",
        pro_number="1Z",
        quote_number="Q1",
        service_days=3,
        handling_units=[{"id": 5, "quantity": 1}],
    )
    data = endpoint.save_final_quote.call_args.kwargs["data"]
    assert "jobModifiedDate" not in data
    assert data["handlingUnits"] == [{"id": 5, "quantity": 1}]
    assert {k: data["quote"][k] for k in ("providerCode", "proNumber", "quoteNumber", "serviceDays")} == {
        "providerCode": "UPS03",
        "proNumber": "1Z",
        "quoteNumber": "Q1",
        "serviceDays": 3,
    }


def test_two_new_overrides_get_different_ids():
    endpoint = _endpoint()
    args = dict(shipping_id=1, shipment_type=PARCEL, provider_id=uuid4(), provider_company_name="x", freight_amount=1)
    assert endpoint.save_new_final_override(1, **args).quote_id != endpoint.save_new_final_override(1, **args).quote_id


def _quote(**overrides):
    created = datetime(2026, 11, 1, tzinfo=timezone.utc)
    values = dict(
        id=str(uuid4()),
        shippingId=11,
        active=True,
        isOverridden=False,
        shipmentAccepted=False,
        orderInShipping=1,
        createdBy=5,
        createdDate=created.isoformat(),
        modifiedBy=5,
        modifiedDate=(created + timedelta(milliseconds=20)).isoformat(),
        freightAmount=12.38,
        providerCompanyName="UPS Ground",
    )
    values.update(overrides)
    return TransportationQuoteResult.model_validate(values)


def test_mark_selected_posts_the_quote_back_unchanged():
    endpoint = _endpoint()
    quote = _quote()
    endpoint.mark_selected(9, quote, job_modified_date="2026-11-23T00:00:00Z")
    data = endpoint.save_final_quote.call_args.kwargs["data"]
    assert data["jobModifiedDate"] == "2026-11-23T00:00:00Z"
    assert data["quote"] == quote.model_dump(by_alias=True, mode="json")
    assert data["quote"]["freightAmount"] == 12.38 and data["quote"]["shipmentAccepted"] is False


def test_mark_selected_refuses_a_quote_without_a_shipping():
    endpoint = _endpoint()
    with pytest.raises(ValueError):
        endpoint.mark_selected(9, _quote(shippingId=None))
    endpoint.save_final_quote.assert_not_called()


def test_a_marked_selection_no_longer_reads_as_an_estimate():
    fresh = _quote()
    assert is_untouched_estimate(fresh, [fresh])
    created = fresh.created_date
    marked = _quote(id=str(fresh.id), modifiedDate=(created + timedelta(minutes=3)).isoformat())
    assert not is_untouched_estimate(marked, [marked])


@pytest.mark.parametrize(
    ("overridden", "accepted", "recorded", "booked"),
    [(True, True, True, False), (False, True, False, True), (True, False, False, False), (False, False, False, False)],
)
def test_quote_state_helpers(overridden, accepted, recorded, booked):
    quote = _quote(isOverridden=overridden, shipmentAccepted=accepted)
    assert is_recorded_override(quote) is recorded
    assert is_carrier_booked(quote) is booked
