"""Deterministic tests for the certification workbench (issue #71).

These drive the *same* functions the notebook calls. If a notebook cell ever
grows logic of its own, it stops being covered here -- which is the point: the
notebook is a UI, this is the contract.

Everything is offline. No network, no credentials, no writes to committed
fixtures or evidence (those paths are redirected to ``tmp_path``).
"""

from __future__ import annotations

import json

import pytest

from ab.progress.certification import MutationClass
from ab.progress.certify import (
    CertificationSession,
    MutationNotClassified,
    approved_constants,
    compare_to_fixture,
    list_endpoints,
    load_response_fixture,
    payload_sha256,
    resolve_route,
    sanitize,
    select_path,
    summarize,
)

# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def test_endpoint_list_is_the_public_denominator() -> None:
    from ab.progress.inventory import public_endpoint_keys

    assert list_endpoints() == list(public_endpoint_keys())
    assert len(list_endpoints()) == 218


def test_endpoint_filter_narrows() -> None:
    assert "api.address.validate" in list_endpoints("address")
    assert all("address" in k for k in list_endpoints("address"))


def test_approved_constants_are_loaded() -> None:
    consts = approved_constants()
    assert consts
    assert "TEST_CONTACT_DID" in consts


def test_unknown_endpoint_is_rejected() -> None:
    with pytest.raises((KeyError, ValueError)):
        resolve_route("api.nope.nothing")


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------


def test_sanitize_is_deterministic() -> None:
    payload = {"firstName": "Dana Whitfield", "email": "dana@test.com", "id": 4821}
    a, ra = sanitize(payload)
    b, rb = sanitize(payload)
    assert a == b
    assert ra.sanitized_sha256 == rb.sanitized_sha256


def test_sanitize_distinguishes_live_from_sanitized_hash() -> None:
    _, report = sanitize({"lastName": "Okafor"})
    assert report.live_sha256 != report.sanitized_sha256
    assert report.was_sanitized


def test_sanitize_preserves_structure_types_and_nullability() -> None:
    payload = {
        "name": "Dana Whitfield",
        "missing": None,
        "flag": True,
        "count": 7,
        "nested": {"email": "a@test.com", "items": [{"phone": "619-555-0134"}]},
    }
    out, report = sanitize(payload)
    assert set(out) == set(payload)
    assert out["missing"] is None
    assert out["flag"] is True
    assert isinstance(out["nested"]["items"], list)
    assert isinstance(out["nested"]["items"][0]["phone"], str)
    assert out["nested"]["email"] != payload["nested"]["email"]
    # A bare `name` is ambiguous -- person, company, or lookup label -- so it is
    # flagged for the operator rather than silently rewritten. It stays as-is in
    # the payload, which is what approve_fixture() refuses to write unattended.
    assert out["name"] == payload["name"]
    assert [d.path for d in report.review] == ["name"]


def test_sanitize_leaves_structural_values_alone() -> None:
    payload = {"status": "Active", "countryCode": "US", "type": "Residential"}
    out, report = sanitize(payload)
    assert out == payload
    assert not report.was_sanitized


def test_sanitize_keeps_email_and_uuid_shapes_valid() -> None:
    import re

    payload = {
        "email": "person@test.com",
        "id": "daf9b34b-ce6a-4f2f-9207-15278c06b7d2",
    }
    out, _ = sanitize(payload)
    assert re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", out["email"])
    assert re.match(r"^[0-9a-f-]{36}$", out["id"])
    assert out["email"] != payload["email"]
    assert out["id"] != payload["id"]


def test_sanitize_preserves_iso_dates() -> None:
    payload = {"noteDate": "2026-07-26T14:00:00"}
    out, _ = sanitize(payload)
    assert out["noteDate"] == payload["noteDate"]


def test_sanitize_redacts_credentials() -> None:
    out, _ = sanitize({"access_token": "eyJhbGciOi.real.secret"})
    assert out["access_token"] == "REDACTED"


def test_payload_hash_is_order_independent() -> None:
    assert payload_sha256({"a": 1, "b": 2}) == payload_sha256({"b": 2, "a": 1})


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------


class _FakeModel:
    """Minimal stand-in with the pydantic surface summarize() touches."""

    model_fields: dict = {}

    def __init__(self, payload):
        self._payload = payload
        self.__pydantic_extra__ = {}

    def model_dump(self, **_):
        return self._payload


def test_summary_never_dumps_the_payload() -> None:
    big = {"items": [{"id": i, "note": "x" * 500} for i in range(200)]}
    s = summarize(_FakeModel(big), big)
    rendered = s.render()
    assert len(rendered) < 600, "summary must stay compact"
    assert "xxxxx" not in rendered
    assert s.item_count == 200
    assert s.json_bytes > 10000


def test_summary_reports_identifiers_and_populated_counts() -> None:
    payload = {"id": 42, "name": "Widget", "empty": None, "blank": ""}
    s = summarize(_FakeModel(payload), payload)
    assert s.identifiers["id"] == 42
    assert s.total == 4
    assert s.populated == 2


def test_full_json_is_bounded_by_default() -> None:
    payload = {"blob": "y" * 50000}
    s = summarize(_FakeModel(payload), payload)
    assert "truncated" in s.full_json()
    assert "truncated" not in s.full_json(max_chars=None)


def test_selected_nested_path() -> None:
    payload = {"items": [{"address": {"city": "Lakemont"}}]}
    assert select_path(payload, "items[0].address.city") == "Lakemont"


def test_extra_fields_are_surfaced() -> None:
    from ab.api.models.address import AddressIsValidResult

    model = AddressIsValidResult.model_validate(
        {**(load_response_fixture("AddressIsValidResult") or {}), "surpriseField": 1}
    )
    s = summarize(model)
    assert "surpriseField" in s.extras
    assert "undeclared" in s.render()


# ---------------------------------------------------------------------------
# Fixture comparison
# ---------------------------------------------------------------------------


def test_fixture_comparison_is_structural_not_value_based() -> None:
    """Sanitized fixtures differ in values by design; shape must still match."""
    live = {"name": "Real Person", "id": 1}
    fixture = {"name": "Avery Holt", "id": 999}
    ok, diffs = compare_to_fixture(live, fixture)
    assert ok and not diffs


def test_fixture_comparison_detects_shape_drift() -> None:
    ok, diffs = compare_to_fixture({"a": 1, "new": 2}, {"a": 1, "gone": 3})
    assert not ok
    assert any("new" in d for d in diffs)
    assert any("gone" in d for d in diffs)


# ---------------------------------------------------------------------------
# Session workflow
# ---------------------------------------------------------------------------


def test_read_only_endpoint_is_preclassified() -> None:
    s = CertificationSession("api.address.validate")
    assert s.mutation_class is MutationClass.READ_ONLY


def test_request_validation_produces_wire_payload() -> None:
    s = CertificationSession("api.address.validate")
    s.validate_request({"line1": "1 A St", "city": "San Diego", "state": "CA", "zip": "92108"})
    # Aliases are what actually go over the wire.
    assert s.request_payload["Line1"] == "1 A St"
    assert s.checks.get("request-model validation").passed


def test_negative_test_passes_when_a_required_field_is_omitted() -> None:
    s = CertificationSession("api.contacts.search")
    required = s.required_fields()
    assert required, "expected ContactSearchRequest to have required fields"
    data = {f: {} for f in required}
    err = s.expect_validation_error(data, omit=required[0])
    assert s.checks.get("expected negative test").passed is True
    assert required[0] in err or "Field required" in err


def test_model_with_no_required_fields_is_not_reported_as_failure() -> None:
    """AddressValidateParams declares everything Optional — that is not a red."""
    s = CertificationSession("api.address.validate")
    s.expect_validation_error({"line1": "x"}, omit="line1")
    check = s.checks.get("expected negative test")
    assert check.passed is None
    assert "no required fields" in check.detail


def test_mutating_endpoint_cannot_execute_before_classification() -> None:
    s = CertificationSession("api.jobs.note.create")
    assert s.mutation_class is None
    with pytest.raises(MutationNotClassified):
        s.execute(lambda: None)


def test_unsafe_for_automation_is_blocked_from_execution() -> None:
    s = CertificationSession("api.jobs.note.create")
    s.classify(MutationClass.UNSAFE_FOR_AUTOMATION)
    with pytest.raises(MutationNotClassified):
        s.execute(lambda: None)


def test_offline_response_recording_produces_green_checks() -> None:
    from ab.api.models.address import AddressIsValidResult

    s = CertificationSession("api.address.validate")
    model = AddressIsValidResult.model_validate(load_response_fixture("AddressIsValidResult"))
    summary = s.record_response(model)
    assert summary.model_type == "AddressIsValidResult"
    assert s.checks.get("response-model validation").passed
    assert s.checks.get("fixture match").passed
    assert s.checks.all_green


def test_fixture_write_requires_explicit_approval(tmp_path, monkeypatch) -> None:
    from ab.api.models.address import AddressIsValidResult
    from ab.progress.certify import session as sess

    # Load the real fixture *before* redirecting the directory — the same
    # constant backs both reads and writes.
    model = AddressIsValidResult.model_validate(
        load_response_fixture("AddressIsValidResult")
    )
    monkeypatch.setattr(sess, "FIXTURES_DIR", tmp_path)
    s = CertificationSession("api.address.validate")
    s.record_response(model)
    s.propose_fixture()
    with pytest.raises(PermissionError):
        s.approve_fixture()
    path = s.approve_fixture(confirm=True)
    assert path.is_file()
    assert json.loads(path.read_text())["isValid"] is True


def test_proposed_fixture_diff_is_reviewable() -> None:
    s = CertificationSession("api.address.validate")
    s.record_response(
        {"email": "person@test.com", "phone": "619-555-0134", "isValid": True}
    )
    report = s.propose_fixture()
    assert report.diff_lines()
    assert all("->" in line for line in report.diff_lines())


def test_proposing_a_clean_capture_is_a_fixed_point() -> None:
    """Re-proposing an already-sanitized fixture must be a no-op.

    Sanitization runs on every capture, including re-captures of unchanged
    responses. If it rewrote its own output the fixture bytes would change on
    each pass and the no-drift gates would thrash on phantom diffs.
    """
    from ab.api.models.address import AddressIsValidResult

    s = CertificationSession("api.address.validate")
    s.record_response(
        AddressIsValidResult.model_validate(load_response_fixture("AddressIsValidResult"))
    )
    report = s.propose_fixture()
    assert report.diff_lines() == []
    assert not report.was_sanitized
    assert not report.needs_review
    assert s.sanitized == s.response_payload


def test_review_flagged_values_block_an_unattended_write(tmp_path, monkeypatch) -> None:
    """A value the sanitizer could not classify is left in the payload verbatim,
    so writing it unattended would commit real data to a public repo."""
    from ab.progress.certify import session as sess

    monkeypatch.setattr(sess, "FIXTURES_DIR", tmp_path)
    s = CertificationSession("api.address.validate")
    s.record_response({"name": "Dana Whitfield", "isValid": True})
    report = s.propose_fixture()
    assert report.needs_review
    assert s.sanitized["name"] == "Dana Whitfield"  # left as-is, not rewritten

    with pytest.raises(PermissionError, match="could not classify"):
        s.approve_fixture(confirm=True)

    path = s.approve_fixture(confirm=True, accept_review=True)
    assert path.is_file()


# ---------------------------------------------------------------------------
# Evidence writing
# ---------------------------------------------------------------------------


@pytest.fixture
def evidence_file(tmp_path, monkeypatch):
    from ab.progress.certify import session as sess

    target = tmp_path / "example_run_results.json"
    monkeypatch.setattr(sess, "RUN_RESULTS", target)
    return target


def test_schema_2_evidence_is_written_without_manual_json(evidence_file) -> None:
    from ab.api.models.address import AddressIsValidResult

    s = CertificationSession("api.address.validate", environment="staging")
    s.record_response(
        AddressIsValidResult.model_validate(load_response_fixture("AddressIsValidResult"))
    )
    s.propose_fixture()
    entry = s.write_evidence()

    data = json.loads(evidence_file.read_text())
    assert data["schema"] == 2
    assert data["results"]["api.address.validate"] == entry
    assert entry["environment"] == "staging"
    assert entry["mutation_class"] == "read_only"
    assert len(entry["fixture_sha256"]) == 64
    # Provenance: the payload went through the sanitizer. A clean capture needs
    # zero rewrites, which is recorded as a count rather than as sanitized=False.
    assert entry["sanitized"] is True
    assert entry["sanitizer_changes"] == 0
    assert entry["sanitizer_review"] == 0
    assert entry["live_sha256"] != entry["fixture_sha256"]


def test_written_hash_is_the_one_the_verifier_checks(evidence_file) -> None:
    """Regression: the workbench once wrote a normalized-JSON hash while
    certification compared a file-bytes hash, so every endpoint went stale the
    instant it was certified. Both sides must use one function.
    """
    from ab.api.models.address import AddressIsValidResult
    from ab.progress.certification import fixture_sha256 as verifier_hash

    s = CertificationSession("api.address.validate")
    s.record_response(
        AddressIsValidResult.model_validate(load_response_fixture("AddressIsValidResult"))
    )
    entry = s.write_evidence()
    assert entry["fixture_sha256"] == verifier_hash("AddressIsValidResult")


def test_evidence_written_by_workbench_reads_back_as_fresh(evidence_file, monkeypatch) -> None:
    """End-to-end: write evidence, then have certification re-read it."""
    from ab.api.models.address import AddressIsValidResult
    from ab.progress import certification as cert

    monkeypatch.setattr(cert, "RUN_RESULTS", evidence_file)
    s = CertificationSession("api.address.validate")
    s.record_response(
        AddressIsValidResult.model_validate(load_response_fixture("AddressIsValidResult"))
    )
    s.write_evidence()

    row = next(
        r for r in cert.build_certification() if r.endpoint_key == "api.address.validate"
    )
    assert row.evidence_state is cert.EvidenceState.FRESH
    assert row.live_verified


def test_evidence_results_stay_sorted(evidence_file) -> None:
    from ab.api.models.address import AddressIsValidResult

    for key in ("api.address.validate", "api.address.get_property_type"):
        s = CertificationSession(key)
        s.record_response(
            AddressIsValidResult.model_validate(
                load_response_fixture("AddressIsValidResult")
            )
        )
        s.propose_fixture()
        s.write_evidence()
    results = json.loads(evidence_file.read_text())["results"]
    assert list(results) == sorted(results)


def test_mutating_endpoint_cannot_write_evidence_without_restoration(evidence_file) -> None:
    s = CertificationSession("api.jobs.note.create")
    s.classify(MutationClass.CIRCULAR_RESTORED)
    with pytest.raises(ValueError, match="restoration evidence"):
        s.write_evidence()


def test_incomplete_restoration_evidence_is_rejected(evidence_file) -> None:
    s = CertificationSession("api.jobs.note.create")
    s.classify(MutationClass.CIRCULAR_RESTORED)
    s.record_restoration(
        record_identifier="ACME_JOB_DISPLAY_ID",
        precondition="no sdk-smoke note",
        mutation="POST note",
        expected_result="created",
        observed_result="created id 1",
        restoration="DELETE note 1",
        final_state_verified=False,  # nobody re-read the record
    )
    assert s.checks.get("restoration").passed is False
    with pytest.raises(ValueError, match="restoration evidence"):
        s.write_evidence()


def test_complete_restoration_evidence_is_accepted(evidence_file) -> None:
    s = CertificationSession("api.jobs.note.create")
    s.classify(MutationClass.CIRCULAR_RESTORED)
    s.record_restoration(
        record_identifier="ACME_JOB_DISPLAY_ID",
        precondition="no sdk-smoke note on the job",
        mutation="POST /job/{id}/note comments='sdk-smoke'",
        expected_result="201, note created",
        observed_result="201, note id 8842",
        restoration="DELETE /job/{id}/note/8842",
        final_state_verified=True,
    )
    assert s.checks.get("restoration").passed is True
    entry = s.write_evidence()
    assert entry["mutation_class"] == "circular_restored"
    assert entry["evidence"]["final_state_verified"] is True
    assert entry["evidence"]["timestamp"]


def test_idempotent_mutation_needs_no_restoration_block(evidence_file) -> None:
    s = CertificationSession("api.notes.update")
    s.classify(MutationClass.IDEMPOTENT)
    entry = s.write_evidence()
    assert entry["mutation_class"] == "idempotent"
    assert "evidence" not in entry


# ---------------------------------------------------------------------------
# Check panel
# ---------------------------------------------------------------------------


def test_check_panel_renders_symbols_and_tracks_failure() -> None:
    s = CertificationSession("api.address.validate")
    s.checks.add("endpoint execution", True, "ok")
    s.checks.add("fixture match", False, "drift")
    s.checks.add("restoration", None, "n/a")
    rendered = s.checks.render()
    assert "✅" in rendered and "❌" in rendered and "—" in rendered
    assert not s.checks.all_green
    assert [c.name for c in s.checks.failed] == ["fixture match"]


def test_checks_are_replaced_not_duplicated() -> None:
    s = CertificationSession("api.address.validate")
    s.checks.add("fixture match", False)
    s.checks.add("fixture match", True)
    assert len([c for c in s.checks.checks if c.name == "fixture match"]) == 1
    assert s.checks.get("fixture match").passed is True
