"""Quote selection reaches HTTP with the correct casing; omission stays compatible."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ab.api.endpoints.jobs.form import JobFormEndpoint
from ab.api.endpoints.jobs.tracking import JobTrackingEndpoint
from ab.api.models.forms import FormQuoteParams
from ab.api.models.jobs import ShipmentTrackingParams

# Synthetic identifiers used only to inspect transport, never as captured fixtures.
QUOTE_ID = "11111111-2222-4333-8444-555555555555"
CASES = [
    (JobFormEndpoint, "packing_slip", (123,), "/job/123/form/packing-slip", "quoteId"),
    (JobFormEndpoint, "packaging_specification", (123,), "/job/123/form/packaging-specification", "quoteId"),
    (JobTrackingEndpoint, "shipment", (123, "test-pro"), "/job/123/tracking/shipment/test-pro", "QuoteId"),
]


@pytest.mark.parametrize("endpoint_cls,method,args,path,alias", CASES)
def test_quote_selector_is_serialized_to_query_not_body(endpoint_cls, method, args, path, alias):
    client = MagicMock()
    client.request.return_value = None
    getattr(endpoint_cls(client), method)(*args, quote_id=QUOTE_ID)
    client.request.assert_called_once_with("GET", path, params={alias: QUOTE_ID})


@pytest.mark.parametrize("endpoint_cls,method,args,path,alias", CASES)
def test_existing_calls_omit_the_selector_instead_of_sending_null(endpoint_cls, method, args, path, alias):
    client = MagicMock()
    client.request.return_value = None
    getattr(endpoint_cls(client), method)(*args)
    client.request.assert_called_once_with("GET", path, params={})


@pytest.mark.parametrize("endpoint_cls,method,args,path,alias", CASES)
def test_invalid_quote_is_rejected_before_http(endpoint_cls, method, args, path, alias):
    client = MagicMock()
    with pytest.raises(ValidationError):
        getattr(endpoint_cls(client), method)(*args, quote_id="not-a-uuid")
    client.request.assert_not_called()


@pytest.mark.parametrize("model,alias", [(FormQuoteParams, "quoteId"), (ShipmentTrackingParams, "QuoteId")])
def test_query_model_accepts_api_alias_and_python_name(model, alias):
    assert model.check({alias: QUOTE_ID}) == {alias: QUOTE_ID}
    assert model.check({"quote_id": QUOTE_ID}) == {alias: QUOTE_ID}
    assert model.check({"quote_id": None}) == {}
    with pytest.raises(ValidationError):
        model.model_validate({"shippingId": QUOTE_ID})
