"""What ``update_task`` actually puts on the wire (issue: PATCH silent no-op).

The live symptom was that ``PATCH /job/{jobDisplayId}/timeline/{timelineTaskId}``
returned **204** and changed nothing: ``modifiedDate`` moved, every requested
value stayed null. A 204 is indistinguishable from success at the call site, so
the endpoint looked healthy while discarding the payload.

The cause is on this side. Swagger's ``UpdateTaskModel`` declares exactly five
properties -- ``truckId``, ``plannedStartDate``, ``preferredStartDate``,
``plannedEndDate``, ``preferredEndDate`` -- each an *override wrapper*
(``{"value": ...}``), and sets ``additionalProperties: false``. The SDK was
sending ``status``, ``scheduledDate``, ``completedDate`` and ``comments``: not
one of them is in the schema, so the server had nothing to apply.

These tests are deterministic and offline. They assert on the serialized request
body, because that is the thing that was wrong -- a test that mocked the
transport and asserted "204 was returned" would have passed throughout.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ab.api.models.jobs import TimelineTaskUpdateRequest

SCHEMA = Path(__file__).resolve().parent.parent.parent / "ab" / "api" / "schemas" / "acportal.json"
PATCH_PATH = "/api/job/{jobDisplayId}/timeline/{timelineTaskId}"


@pytest.fixture(scope="module")
def update_task_model() -> dict:
    spec = json.loads(SCHEMA.read_text(encoding="utf-8"))
    ref = spec["paths"][PATCH_PATH]["patch"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    return spec["components"]["schemas"][ref.rsplit("/", 1)[-1]]


def _wire(**kwargs) -> dict:
    """Exactly what the endpoint method passes as the JSON body."""
    return TimelineTaskUpdateRequest(**kwargs).model_dump(
        by_alias=True, mode="json", exclude_none=True
    )


def test_swagger_declares_only_wrapped_date_and_truck_fields(update_task_model) -> None:
    """Pin the contract this model has to satisfy."""
    assert set(update_task_model["properties"]) == {
        "truckId",
        "plannedStartDate",
        "preferredStartDate",
        "plannedEndDate",
        "preferredEndDate",
    }
    assert update_task_model["additionalProperties"] is False


def test_every_field_the_sdk_sends_exists_in_the_schema(update_task_model) -> None:
    """The regression itself: unknown properties are silently dropped.

    ``additionalProperties: false`` plus a 204 means a body of entirely unknown
    keys is accepted and ignored — there is no error to notice.
    """
    allowed = set(update_task_model["properties"])
    sent = set(
        _wire(
            plannedStartDate="2026-08-05T14:00:00",
            preferredStartDate="2026-08-05T15:00:00",
            plannedEndDate="2026-08-06T10:00:00",
            preferredEndDate="2026-08-06T11:00:00",
            truckId=7,
        )
    )
    unknown = sent - allowed
    assert not unknown, f"SDK sends properties the API will discard: {sorted(unknown)}"


def test_dates_are_serialized_as_override_wrappers() -> None:
    """Each date is ``{"value": ...}``, not a bare scalar.

    A bare ISO string is a well-formed JSON value of the wrong *shape*: it does
    not match UpdateDateModel, so it lands in the same silent-discard path.
    """
    body = _wire(plannedStartDate="2026-08-05T14:00:00")
    assert body == {"plannedStartDate": {"value": "2026-08-05T14:00:00"}}


def test_truck_id_is_an_override_wrapper_too() -> None:
    assert _wire(truckId=7) == {"truckId": {"value": 7}}


def test_omitted_fields_are_absent_not_null() -> None:
    """A PATCH must not blank fields the caller never mentioned."""
    body = _wire(plannedEndDate="2026-08-06T10:00:00")
    assert body == {"plannedEndDate": {"value": "2026-08-06T10:00:00"}}


def test_explicit_null_clears_a_date() -> None:
    """``{"value": null}`` is how the contract expresses "clear this"."""
    body = TimelineTaskUpdateRequest(plannedStartDate=None).model_dump(
        by_alias=True, mode="json", exclude_unset=True
    )
    assert body == {"plannedStartDate": {"value": None}}


def test_the_dropped_legacy_fields_are_gone() -> None:
    """status/scheduledDate/completedDate/comments were never in the contract.

    Named explicitly so the mistake cannot quietly return.
    """
    declared = set(TimelineTaskUpdateRequest.model_fields)
    aliases = {f.alias for f in TimelineTaskUpdateRequest.model_fields.values() if f.alias}
    for gone in ("status", "scheduled_date", "completed_date", "comments"):
        assert gone not in declared, f"{gone} is not part of UpdateTaskModel"
    for gone in ("scheduledDate", "completedDate", "comments"):
        assert gone not in aliases, f"{gone} is not part of UpdateTaskModel"
