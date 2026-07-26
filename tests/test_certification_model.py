"""Certification semantics: presence must never be reported as proof (issue #69).

These tests encode the distinctions the old report collapsed. Each one would
have passed trivially under the previous model, which is the point: they pin
the *separation* between structural presence and live verification, not the
current counts (those are expected to move as evidence is captured).
"""

from __future__ import annotations

from ab.progress.certification import (
    EndpointCertification,
    EvidenceState,
    MutationClass,
    MutationEvidence,
    build_certification,
    certification_summary,
)


def _row(**kw) -> EndpointCertification:
    """A structurally complete, operator-ready read-only row; override per test."""
    base = dict(
        endpoint_key="api.demo.get",
        http_method="GET",
        path="/demo/{id}",
        response_model="DemoModel",
        has_example=True,
        has_fixture=True,
        has_model_test=True,
        has_sphinx=True,
        shared_constants=("TEST_DEMO_ID",),
        evidence_state=EvidenceState.FRESH,
        mutation_class=MutationClass.READ_ONLY,
    )
    base.update(kw)
    return EndpointCertification(**base)


# ---------------------------------------------------------------------------
# The core separation
# ---------------------------------------------------------------------------


def test_structural_completeness_alone_is_not_certification() -> None:
    """Every file present, but nothing ever ran -> not certified."""
    r = _row(evidence_state=EvidenceState.MISSING)
    assert r.structurally_complete
    assert r.operator_ready
    assert not r.live_verified
    assert not r.certified
    assert "no run evidence" in r.blockers()


def test_fixture_and_doc_presence_do_not_imply_execution() -> None:
    r = _row(evidence_state=EvidenceState.MISSING)
    assert r.has_fixture and r.has_sphinx
    assert not r.live_verified


def test_stale_evidence_is_not_live_verified() -> None:
    r = _row(evidence_state=EvidenceState.STALE)
    assert not r.live_verified
    assert not r.certified
    assert any("stale" in b for b in r.blockers())


def test_failing_evidence_is_not_live_verified() -> None:
    r = _row(evidence_state=EvidenceState.FAILING)
    assert not r.live_verified
    assert "run evidence failing" in r.blockers()


def test_binary_response_still_requires_evidence_that_it_ran() -> None:
    """'Returns bytes' waives the fixture diff, not the execution."""
    missing = _row(response_model="bytes", evidence_state=EvidenceState.MISSING)
    assert not missing.live_verified

    ran = _row(response_model="bytes", evidence_state=EvidenceState.BINARY_VERIFIED)
    assert ran.live_verified


# ---------------------------------------------------------------------------
# Operator readiness
# ---------------------------------------------------------------------------


def test_operator_ready_requires_an_approved_shared_constant() -> None:
    r = _row(shared_constants=(), needs_record_identifier=True)
    assert not r.operator_ready
    assert "no approved shared constant" in r.blockers()


def test_endpoint_without_path_parameter_needs_no_constant() -> None:
    r = _row(path="/demo", shared_constants=(), needs_record_identifier=False)
    assert r.operator_ready


def test_missing_example_is_never_operator_ready() -> None:
    assert not _row(has_example=False).operator_ready


# ---------------------------------------------------------------------------
# Mutation and restoration
# ---------------------------------------------------------------------------


def _complete_evidence(**kw) -> MutationEvidence:
    base = dict(
        record_identifier="TEST_JOB_DISPLAY_ID",
        environment="staging",
        precondition="note absent",
        mutation="POST note",
        expected_result="note created",
        observed_result="note created, id 42",
        restoration="DELETE note 42",
        final_state_verified=True,
        timestamp="2026-07-26T00:00:00Z",
    )
    base.update(kw)
    return MutationEvidence(**base)


def test_mutating_endpoint_needs_restoration_evidence() -> None:
    r = _row(
        http_method="POST",
        mutation_class=MutationClass.CIRCULAR_RESTORED,
        evidence=None,
    )
    assert not r.restoration_verified
    assert not r.certified
    assert "no restoration evidence" in r.blockers()


def test_complete_restoration_evidence_certifies_a_mutating_endpoint() -> None:
    r = _row(
        http_method="POST",
        mutation_class=MutationClass.CIRCULAR_RESTORED,
        evidence=_complete_evidence(),
    )
    assert r.restoration_verified
    assert r.certified


def test_partial_restoration_evidence_is_rejected_and_names_gaps() -> None:
    r = _row(
        http_method="POST",
        mutation_class=MutationClass.CIRCULAR_RESTORED,
        evidence=_complete_evidence(restoration=None, observed_result=None),
    )
    assert not r.restoration_verified
    blockers = " ".join(r.blockers())
    assert "restoration" in blockers and "observed_result" in blockers


def test_final_state_must_actually_be_verified() -> None:
    """Every narrative field filled in, but nobody re-read the record."""
    r = _row(
        http_method="POST",
        mutation_class=MutationClass.CIRCULAR_RESTORED,
        evidence=_complete_evidence(final_state_verified=False),
    )
    assert not r.restoration_verified


def test_idempotent_mutation_is_self_restoring() -> None:
    r = _row(http_method="PUT", mutation_class=MutationClass.IDEMPOTENT)
    assert r.restoration_verified
    assert r.certified


def test_unsafe_for_automation_can_never_certify() -> None:
    r = _row(
        http_method="DELETE",
        mutation_class=MutationClass.UNSAFE_FOR_AUTOMATION,
        evidence=_complete_evidence(),
    )
    assert not r.restoration_verified
    assert not r.certified
    assert "unsafe for automation" in r.blockers()


def test_read_only_endpoint_does_not_need_restoration() -> None:
    r = _row(mutation_class=MutationClass.READ_ONLY)
    assert r.restoration_verified  # not applicable
    assert r.certified


# ---------------------------------------------------------------------------
# Live build
# ---------------------------------------------------------------------------


def test_live_build_covers_the_public_denominator() -> None:
    from ab.progress.inventory import reconcile

    rows = build_certification()
    assert len(rows) == reconcile().public_count
    assert {r.endpoint_key for r in rows} == set(reconcile().public_endpoint_keys)


def test_summary_reports_structural_and_live_separately() -> None:
    """The two must never be merged into a single completion number."""
    s = certification_summary(build_certification())
    assert "structurally_complete" in s
    assert "live_verified" in s
    assert "certified" in s
    # Certification can never exceed either input.
    assert s["certified"] <= s["structurally_complete"]
    assert s["certified"] <= s["live_verified"]


def test_no_endpoint_is_certified_without_evidence() -> None:
    """Whole-repo invariant: certification requires committed run evidence."""
    for r in build_certification():
        if r.certified:
            assert r.live_verified, f"{r.endpoint_key} certified without live evidence"


def test_model_test_signal_is_per_model_not_per_file() -> None:
    """Regression: file-level coverage marked every method in a module tested.

    A model with no test of its own must not inherit a sibling's signal.
    """
    from ab.progress.certification import model_tested_names

    tested = model_tested_names()
    assert tested, "model-test scan found nothing — signal is blind"
    rows = build_certification()
    assert not all(r.has_model_test for r in rows), (
        "every endpoint reports a model test — the signal is file-level again"
    )
