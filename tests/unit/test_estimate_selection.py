"""Synthetic tests for telling an untouched estimate from a selected rate."""

from datetime import datetime, timedelta, timezone

import pytest

from ab.api.models.release_support import TransportationQuoteResult
from ab.api.selection import is_untouched_estimate

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
A, B = "11111111-2222-4333-8444-555555555555", "99999999-2222-4333-8444-555555555555"


def _quote(**fields):
    base = {
        "id": A, "shippingId": 7, "active": True, "isOverridden": False, "shipmentAccepted": False,
        "orderInShipping": 1, "createdBy": 206, "createdDate": T0, "modifiedBy": 206, "modifiedDate": T0,
    }
    return TransportationQuoteResult.model_validate({**base, **fields})


def test_a_new_sole_unmodified_quote_is_an_estimate():
    quote = _quote(modifiedDate=T0 + timedelta(milliseconds=40))
    assert is_untouched_estimate(quote, [quote, _quote(id=B, shippingId=8)])


def test_a_migrated_quote_is_judged_without_its_substituted_created_date():
    migrated = dict(createdBy=None, createdDate=datetime.now(timezone.utc), modifiedBy=None, modifiedDate=None)
    quote = _quote(**migrated)
    assert is_untouched_estimate(quote, [quote])
    saved = _quote(**{**migrated, "modifiedBy": 206, "modifiedDate": datetime.now(timezone.utc)})
    assert not is_untouched_estimate(saved, [saved])


@pytest.mark.parametrize(
    "fields",
    [
        {"shipmentAccepted": True},
        {"isOverridden": True},
        {"orderInShipping": 2},
        {"active": False},
        {"shippingId": None},
        {"modifiedDate": T0 + timedelta(minutes=3)},  # saved as final later
        {"createdDate": None},
        {"createdDate": T0.replace(tzinfo=None)},  # stamps that cannot be compared
        {"modifiedDate": None},  # created on 8_01 but a modifier is recorded with no date
    ],
)
def test_anything_superseded_touched_acted_on_or_doubtful_is_a_selection(fields):
    quote = _quote(**fields)
    assert not is_untouched_estimate(quote, [quote])


def test_another_quote_in_the_shipping_or_a_missing_listing_makes_it_a_selection():
    quote = _quote()
    assert not is_untouched_estimate(quote, [quote, _quote(id=B, active=False)])
    assert not is_untouched_estimate(quote, [])
