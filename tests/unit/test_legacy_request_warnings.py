"""Supported requests warn visibly without announcing deprecation or removal."""

import warnings
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ab import LegacyRequestWarning
from ab.api.endpoints.jobs.parcel_items import JobParcelItemsEndpoint
from ab.api.endpoints.jobs.shipment import JobShipmentEndpoint
from ab.api.models.packing import Shipping
from ab.api.selection import select_shipping

QUOTE = "11111111-2222-4333-8444-555555555555"


def test_supported_parcel_read_emits_one_caller_attributed_filterable_warning():
    client = MagicMock()
    client.request.return_value = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert JobParcelItemsEndpoint(client).list(123) == []
    assert len(caught) == 1
    assert caught[0].category is LegacyRequestWarning
    assert Path(caught[0].filename) == Path(__file__)
    assert "jobs.handling_units.get_all()" in str(caught[0].message)
    assert "no removal is scheduled" in str(caught[0].message)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("ignore", LegacyRequestWarning)
        JobParcelItemsEndpoint(client).list(123)
    assert not caught


def test_explicit_booking_does_not_emit_legacy_warning():
    client = MagicMock()
    client.request.return_value = {"success": True}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        JobShipmentEndpoint(client).book_v2(123, quote_id=QUOTE)
    assert not caught


@pytest.mark.parametrize(
    "records,selectors",
    [
        ([], {}),
        ([{"id": 1, "isArchived": False}, {"id": 2, "isArchived": False}], {}),
        ([{"id": 1, "isArchived": True}], {"shipping_id": 1}),
        ([{"id": 1, "isArchived": False}], {"shipping_id": 2}),
        (
            [{"id": 1, "isArchived": False, "freightQuoteOptions": [QUOTE]}, {"id": 2, "isArchived": False}],
            {"shipping_id": 2, "quote_id": QUOTE},
        ),
        ([{"id": 1}], {}),  # an absent archive flag is not proof of an active record
    ],
)
def test_ambiguous_archived_missing_or_conflicting_selection_is_rejected(records, selectors):
    with pytest.raises(ValueError):
        select_shipping([Shipping.model_validate(r) for r in records], **selectors)


def test_selection_preserves_all_records_and_uses_the_requested_quote():
    records = [
        Shipping(id=1, is_archived=False),
        Shipping(id=2, is_archived=False, freight_quote_options=[QUOTE]),
        Shipping(id=3, is_archived=True),
    ]
    assert select_shipping(records, shipping_id=2, quote_id=QUOTE) is records[1]
    assert len(records) == 3
    assert select_shipping([records[0]]) is records[0]


@pytest.mark.parametrize(
    "method,kwargs", [("book", {"data": {}}), ("delete", {}), ("post_export_data", {"data": {"customsValue": 10}})]
)
def test_legacy_mutations_refuse_multiple_active_shippings(method, kwargs):
    client = MagicMock()
    client.request.return_value = [{"id": 1, "isArchived": False}, {"id": 2, "isArchived": False}]
    with pytest.warns(LegacyRequestWarning), pytest.raises(ValueError, match="Exactly one active"):
        getattr(JobShipmentEndpoint(client), method)(123, **kwargs)
    client.request.assert_called_once_with("GET", "/job/123/shippings")


def test_legacy_quote_option_index_is_not_silently_ignored():
    client = MagicMock()
    with pytest.warns(LegacyRequestWarning), pytest.raises(ValueError, match="quoteOptionIndex"):
        JobShipmentEndpoint(client).book(123, data={"quoteOptionIndex": 1})
    client.request.assert_not_called()
