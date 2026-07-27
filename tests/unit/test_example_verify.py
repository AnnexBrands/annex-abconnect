"""Unit tests for the example/fixture comparison policy (feature 037, T015)."""

from __future__ import annotations

from ab.progress.example_verify import compare, normalize


def test_identical_payloads_match() -> None:
    a = {"id": 1, "name": "x", "items": [{"k": "v"}]}
    matches, detail = compare(a, dict(a))
    assert matches is True
    assert detail is None


def test_volatile_only_difference_matches() -> None:
    fixture = {"id": 1, "name": "x", "createdDate": "2026-01-01T00:00:00Z", "correlationId": "a"}
    produced = {"id": 1, "name": "x", "createdDate": "2026-06-06T12:00:00Z", "correlationId": "b"}
    matches, detail = compare(produced, fixture)
    assert matches is True, detail


def test_nested_and_underscore_date_keys_are_dropped() -> None:
    assert normalize({"modified_at_time": 1, "keep": 2}) == {"keep": 2}
    assert normalize({"a": {"updatedDateTime": 1, "b": 3}}) == {"a": {"b": 3}}


def test_value_difference_alone_is_not_a_failure() -> None:
    """Committed fixtures are sanitized, so their values differ from live by
    design. Comparing by value reported every sanitized endpoint as failing."""
    matches, detail = compare({"id": 2, "name": "y"}, {"id": 1, "name": "x"})
    assert matches is True
    assert detail is None


def test_type_difference_fails_with_detail() -> None:
    matches, detail = compare({"id": "2"}, {"id": 1})
    assert matches is False
    assert detail and "id" in detail


def test_list_length_difference_is_not_a_failure() -> None:
    """How many rows the test account happens to hold is not a contract change."""
    matches, _ = compare({"items": [1, 2, 3]}, {"items": [1, 2]})
    assert matches is True


def test_list_element_type_difference_fails() -> None:
    matches, detail = compare({"items": ["a"]}, {"items": [1]})
    assert matches is False
    assert detail and "items[]" in detail


def test_detail_is_capped() -> None:
    big_fixture = {f"k{i}": i for i in range(200)}
    big_produced = {f"k{i}": str(i) for i in range(200)}
    matches, detail = compare(big_produced, big_fixture)
    assert matches is False
    assert detail.count("\n") <= 41  # capped at _MAX_DETAIL_LINES + trailer
