"""Synthetic contract tests for the BOL convenience helpers on 8_01 leg names."""

import warnings
from unittest.mock import MagicMock

import pytest

from ab import LegacyRequestWarning
from ab.api.endpoints.jobs.form import JobFormEndpoint

Q1 = "11111111-2222-4333-8444-555555555555"
Q2 = "99999999-2222-4333-8444-555555555555"
PICKUP, CARRIER, HOUSE, DELIVERY = (f"0000000{n}-0000-4000-8000-000000000000" for n in range(1, 5))


def _plan(leg, plan_id, quote=None):
    return {"transportType": leg, "jobShipmentID": plan_id, "freightQuoteOptionsId": quote}


def _endpoint(plans):
    client = MagicMock()
    client.request.side_effect = lambda method, path, **kw: plans if path.endswith("/form/shipments") else b"%PDF-"
    return JobFormEndpoint(client), client


def _bol_params(client):
    return next(c for c in client.request.call_args_list if c.args[1].endswith("/bill-of-lading")).kwargs["params"]


PLANS = [
    _plan("PickUp", PICKUP),
    _plan("PickUp (LTL)", CARRIER, Q1),
    _plan("House", HOUSE),
    _plan("Delivery", DELIVERY),
]


def test_bol_uses_the_carrier_leg_and_its_active_quote():
    endpoint, client = _endpoint(PLANS)
    with warnings.catch_warnings():
        warnings.simplefilter("error", LegacyRequestWarning)
        assert endpoint.bol(123) == {"bol_123.pdf": b"%PDF-"}
    assert _bol_params(client) == {"shipmentPlanId": CARRIER, "quoteId": Q1}


def test_bol_with_two_active_quotes_requires_the_quote_to_be_named():
    plans = [_plan("PickUp", PICKUP), _plan("PickUp (PARCEL)", CARRIER, Q1), _plan("PickUp (PARCEL)", CARRIER, Q2)]
    endpoint, client = _endpoint(plans)
    with pytest.raises(ValueError, match="exactly one PickUp shipment plan"):
        endpoint.bol(123)
    endpoint.bol(123, quote_id=Q2)
    assert _bol_params(client) == {"shipmentPlanId": CARRIER, "quoteId": Q2}


@pytest.mark.parametrize("helper,plan_id", [("hbl", HOUSE), ("pbl", PICKUP), ("dbl", DELIVERY)])
def test_agent_and_house_helpers_pick_their_leg_and_pass_a_quote_through(helper, plan_id):
    endpoint, client = _endpoint(PLANS)
    with pytest.warns(LegacyRequestWarning, match=f"jobs.form.{helper}"):
        getattr(endpoint, helper)(123)
    assert _bol_params(client) == {"shipmentPlanId": plan_id}
    client.reset_mock()
    getattr(endpoint, helper)(123, quote_id=Q1)
    assert _bol_params(client) == {"shipmentPlanId": plan_id, "quoteId": Q1}


def test_dbl_needs_an_ltl_carrier_leg_and_legacy_leg_names_still_work():
    endpoint, _ = _endpoint([_plan("PickUp (PARCEL)", CARRIER, Q1), _plan("Delivery", DELIVERY)])
    with pytest.raises(ValueError, match="No LTL shipment plan"):
        endpoint.dbl(123)
    endpoint, client = _endpoint([_plan("LTL", CARRIER, Q1), _plan("Delivery", DELIVERY)])
    endpoint.bol(123)
    assert _bol_params(client) == {"shipmentPlanId": CARRIER, "quoteId": Q1}
