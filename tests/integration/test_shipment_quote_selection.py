"""Opt-in read-only validation using a provisioned job, quote, and carrier PRO."""

import os

import pytest

from ab.api.models.jobs import ShipmentTrackingDetails
from tests.conftest import assert_no_extra_fields

pytestmark = pytest.mark.live


@pytest.fixture
def quote_selection():
    job = os.getenv("AB_TEST_SHIPMENT_JOB_ID")
    quote = os.getenv("AB_TEST_QUOTE_ID")
    if not job or not quote:
        pytest.skip("Set AB_TEST_SHIPMENT_JOB_ID and AB_TEST_QUOTE_ID to a provisioned staging shipment")
    return int(job), quote


@pytest.mark.parametrize("method", ["packing_slip", "packaging_specification"])
def test_quote_selected_form_is_pdf(quote_selection, api, method):
    job, quote = quote_selection
    result = getattr(api.jobs.form, method)(job, quote_id=quote)
    assert len(result) == 1
    assert next(iter(result.values())).startswith(b"%PDF-")


def test_quote_selected_tracking_matches_model(quote_selection, api):
    pro = os.getenv("AB_TEST_PRO_NUMBER")
    if not pro:
        pytest.skip("Set AB_TEST_PRO_NUMBER for the same job and quote")
    job, quote = quote_selection
    result = api.jobs.tracking.shipment(job, pro, quote_id=quote)
    assert isinstance(result, ShipmentTrackingDetails)
    assert_no_extra_fields(result)
