"""Tests for ``api.jobs.items`` — lenient parcel/freight item helpers.

Covers the lifecycle the helpers were added for: create-then-delete,
create-then-replace, and that a follow-up GET shows the expected state. Also
pins the "don't squawk" guarantee: loose kwargs the request model doesn't
declare are dropped instead of raising, and a fully-populated freight payload
validates with no ResponseModel drift warning.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

from ab.api.models.jobs import JobFreightItem, ParcelItem
from ab.api.models.shared import ServiceBaseResponse

JOB = 7009964


# ---- Parcel items ----------------------------------------------------------


def _parcel_jobs() -> MagicMock:
    jobs = MagicMock()
    jobs.parcel_items.create.side_effect = lambda jid, *, data: ParcelItem(
        id=999, description=data["description"], quantity=data.get("quantity")
    )
    jobs.parcel_items.delete.return_value = ServiceBaseResponse(success=True)
    jobs.update_item.return_value = ServiceBaseResponse(success=True)
    return jobs










# ---- Freight items (stateful fake -> exercises get-merge-write) -------------


class _FakeFreightJobs:
    """Models the server's replace-all freight behaviour for round-trip tests."""

    def __init__(self, items: list[dict] | None = None) -> None:
        self._state: list[dict] = list(items or [])
        self.saved_payloads: list[list[dict]] = []

    def get(self, job_display_id: int):
        freight = [JobFreightItem.model_validate(d) for d in self._state]
        return SimpleNamespace(freight_items=freight)

    def add_freight_items(self, job_display_id: int, *, data: dict) -> None:
        payload = data["freightItems"]
        self.saved_payloads.append(payload)
        self._state = [dict(d) for d in payload]  # server replaces the whole set










# ---- "Don't squawk": full payload validates with no drift warning ----------


def test_full_freight_payload_validates_without_drift_warning(caplog):
    payload = {
        "itemID": "i", "jobID": "j", "jobDisplayId": "7009964", "freightItemId": "fi",
        "freightItemClassId": "fc", "jobFreightID": "jf", "quantity": 2,
        "itemLength": 10.0, "itemWidth": 5.0, "itemHeight": 4.0, "itemWeight": 100.0,
        "itemValue": 500.0, "totalWeight": 200.0, "cube": 1.2, "netCubicFeet": 1.2,
        "netCubicInches": 2000, "longestDimension": 10.0, "transportationLength": 10,
        "transportationWidth": 5, "transportationHeight": 4, "ceilingTransportationWeight": 210,
        "freightDescription": "Crate", "freightItemValue": "500", "freightItemClass": "70",
        "nmfcItem": "12345", "bolDescription": "bol", "jobFreightReport": "r",
        "createdBy": "u", "createdDate": "2026-01-01T00:00:00Z", "modifiedBy": "u",
        "modifiedDate": "2026-01-02T00:00:00Z",
    }

    with caplog.at_level(logging.WARNING, logger="ab.api.models.base"):
        model = JobFreightItem.model_validate(payload)

    assert not model.model_extra  # every server field is declared
    assert "consider adding it to the model" not in caplog.text
