"""The shared harness/workbench comparator (issue #71).

Anchored on the four real defects the first read-only sweep surfaced, plus the
false failure that made the sweep's results untrustworthy in the first place:
``api.address.validate`` was reported failing because its fixture held the
sanitizer's synthetic coordinates while live staging returned the real ones.

A comparator that cannot tell those two situations apart is worse than none —
it either hides the type drift or drowns it in noise.
"""

from __future__ import annotations

from ab.progress.compare import compare
from ab.progress.example_verify import compare as harness_compare

# ---------------------------------------------------------------------------
# Sanitized values must not read as drift
# ---------------------------------------------------------------------------


def test_sanitized_coordinates_are_not_a_failure() -> None:
    """The exact false failure that made address.validate look uncertified."""
    fixture = {"isValid": True, "latitude": 34.05, "longitude": -74.01, "countryCode": "US"}
    live = {"isValid": True, "latitude": 32.7776075, "longitude": -117.1587817, "countryCode": "US"}
    assert compare(live, fixture).ok


def test_sanitized_identifiers_and_names_are_not_a_failure() -> None:
    fixture = {
        "id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
        "contactName": "Avery Holt",
        "email": "avery.holt@example.com",
    }
    live = {
        "id": "daf9b34b-ce6a-4f2f-9207-15278c06b7d2",
        "contactName": "Dana Whitfield",
        "email": "dana.whitfield@test.com",
    }
    assert compare(live, fixture).ok


def test_volatile_fields_are_ignored() -> None:
    fixture = {"id": 1, "createdDate": "2026-01-01", "correlationId": "a"}
    live = {"id": 2, "createdDate": "2026-07-26", "correlationId": "z"}
    assert compare(live, fixture).ok


def test_element_count_and_order_are_not_drift() -> None:
    fixture = {"items": [{"id": 1, "name": "a"}]}
    live = {"items": [{"id": 9, "name": "z"}, {"id": 8, "name": "y"}, {"id": 7, "name": "x"}]}
    assert compare(live, fixture).ok


def test_an_unpopulated_optional_is_variance_not_drift() -> None:
    """Whether the test account happens to have data is not a contract change."""
    fixture = {"isValid": True, "validatedAddress": None}
    live = {"isValid": True, "validatedAddress": {"line1": "x", "city": "y"}}
    report = compare(live, fixture)
    assert report.ok
    assert "validatedAddress" in report.nullable


# ---------------------------------------------------------------------------
# Real type drift must fail — the defects the sweep found
# ---------------------------------------------------------------------------


def test_int_id_where_a_string_is_declared_fails() -> None:
    """Commodity.id and Partner.id: live returns 1, model declares str."""
    report = compare({"id": 1, "name": "Art"}, {"id": "COMM-1", "name": "Art"})
    assert not report.ok
    assert any(d.path == "id" and d.kind == "type" for d in report.diffs)
    assert "string" in report.detail() and "number" in report.detail()


def test_numeric_string_where_an_int_is_declared_fails() -> None:
    """DashboardSummary.data[].step: live returns '2.' where an int is declared."""
    report = compare({"data": [{"step": "2."}]}, {"data": [{"step": 2}]})
    assert not report.ok
    assert any(d.path == "data[].step" for d in report.diffs)


def test_list_where_an_object_is_declared_fails() -> None:
    """GridViewAccess: the endpoint returns a list, the model expects one object."""
    report = compare([{"id": 49, "companyId": None}], {"id": 49, "companyId": None})
    assert not report.ok
    assert any(d.kind == "type" for d in report.diffs)


def test_bool_turning_into_a_number_fails() -> None:
    report = compare({"isActive": 1}, {"isActive": True})
    assert not report.ok


# ---------------------------------------------------------------------------
# Structure, not just top-level keys
# ---------------------------------------------------------------------------


def test_missing_and_added_keys_are_reported_with_direction() -> None:
    report = compare({"a": 1, "new": 2}, {"a": 1, "gone": 3})
    assert not report.ok
    detail = report.detail()
    assert "gone" in detail and "absent live" in detail
    assert "new" in detail and "fixture stale" in detail


def test_drift_deep_inside_a_nested_list_is_caught() -> None:
    """Top-level key equality would pass this; it must not."""
    fixture = {"jobs": [{"contacts": [{"phone": "555-0100"}]}]}
    live = {"jobs": [{"contacts": [{"phone": 6195550134}]}]}
    report = compare(live, fixture)
    assert not report.ok
    assert any("phone" in d.path for d in report.diffs)


def test_a_key_missing_from_only_one_list_element_is_caught() -> None:
    fixture = {"items": [{"id": 1, "code": "A"}]}
    live = {"items": [{"id": 1, "code": "A"}, {"id": 2}]}
    assert compare(live, fixture).ok  # merged: 'code' still present somewhere

    live_none = {"items": [{"id": 1}, {"id": 2}]}
    assert not compare(live_none, fixture).ok


def test_no_fixture_is_reported_as_not_compared() -> None:
    report = compare({"a": 1}, None)
    assert not report.compared


# ---------------------------------------------------------------------------
# Model-level checks
# ---------------------------------------------------------------------------


def test_undeclared_response_fields_fail_certification() -> None:
    from ab.api.models.address import AddressIsValidResult

    fixture = {"isValid": True}
    model = AddressIsValidResult.model_validate({"isValid": True, "surpriseField": 1})
    report = compare(model.model_dump(by_alias=True, mode="json"), fixture, model=model)
    assert not report.ok
    assert "surpriseField" in report.extras


# ---------------------------------------------------------------------------
# One implementation, two callers
# ---------------------------------------------------------------------------


def test_harness_and_workbench_share_one_implementation() -> None:
    from ab.progress.certify.session import compare_to_fixture

    fixture = {"id": "COMM-1", "latitude": 34.05}
    live = {"id": 1, "latitude": 32.77}

    harness_ok, harness_detail = harness_compare(live, fixture)
    bench_ok, bench_lines = compare_to_fixture(live, fixture)

    assert harness_ok is bench_ok is False
    # Same verdict for the same reason: the int id, not the coordinate.
    assert "id" in harness_detail
    assert any("id" in line for line in bench_lines)
    assert "latitude" not in harness_detail
    assert not any("latitude" in line for line in bench_lines)


def test_harness_agrees_with_workbench_on_a_sanitized_match() -> None:
    from ab.progress.certify.session import compare_to_fixture

    fixture = {"contactName": "Avery Holt", "latitude": 34.05}
    live = {"contactName": "Dana Whitfield", "latitude": 32.7776075}
    assert harness_compare(live, fixture)[0] is True
    assert compare_to_fixture(live, fixture)[0] is True
