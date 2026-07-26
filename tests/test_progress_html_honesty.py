"""The rendered artifact must not contradict itself (issue #69).

The previous report showed "Coverage Summary … 100% Done" and "73% complete"
at the top while its own Paste Capture section said ``0 filled / 103 awaiting
paste`` underneath. These tests pin the summary against the row-level data it
is rendered from, so the two can never drift apart again.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ab.progress.certification import build_certification, certification_summary

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT = REPO_ROOT / "html" / "progress.html"


@pytest.fixture(scope="module")
def html() -> str:
    if not REPORT.is_file():
        pytest.skip("html/progress.html not generated")
    return REPORT.read_text(encoding="utf-8")


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))


def test_certification_panel_is_present_and_first(html: str) -> None:
    """Certification must lead; the inventory panel must not be the headline."""
    cert = html.find("Certification Status")
    inventory = html.find("Implementation Inventory")
    assert cert != -1, "Certification Status panel missing"
    assert inventory != -1, "Implementation Inventory panel missing"
    assert cert < inventory, "inventory is rendered above certification"


def test_no_bare_completion_headline(html: str) -> None:
    """Regression: the old '171 of 235 complete' headline must not return."""
    body = _text(html)
    assert "of 235 complete" not in body
    assert "Coverage Summary" not in body


def test_gate_panel_is_labelled_structural_conformance(html: str) -> None:
    body = _text(html)
    assert "Structural Conformance" in body
    assert "Quality Gate Status" not in body


def test_summary_counts_match_the_live_certification_data(html: str) -> None:
    """Every rendered ladder count must equal what the model computes."""
    s = certification_summary(build_certification())
    body = _text(html)
    for key, label in (
        ("implemented", "Implemented"),
        ("structurally_complete", "Structurally complete"),
        ("operator_ready", "Operator ready"),
        ("live_verified", "Live verified"),
        ("certified", "Certified"),
    ):
        expected = f"{s[key]}/{s['total']}"
        assert expected in body, (
            f"{label} should render as {expected}; summary and report disagree"
        )


def test_evidence_counts_are_surfaced(html: str) -> None:
    """Missing and stale evidence must be visible, not hidden behind a green %."""
    s = certification_summary(build_certification())
    body = _text(html)
    assert f"{s['evidence_missing']} missing" in body
    assert f"{s['evidence_stale']} stale" in body


def test_report_states_that_structure_is_not_proof(html: str) -> None:
    """The caveat distinguishing presence from execution must be present."""
    body = _text(html)
    assert "not proof of execution" in body


def test_paste_capture_does_not_contradict_the_summary(html: str) -> None:
    """Endpoints awaiting data must not be counted as live verified."""
    m = re.search(r"(\d+) filled / (\d+) awaiting paste", _text(html))
    if not m:
        pytest.skip("paste capture panel not rendered")
    awaiting = int(m.group(2))
    s = certification_summary(build_certification())
    assert s["live_verified"] + awaiting <= s["total"], (
        "live-verified plus awaiting-paste exceeds the endpoint total — "
        "the summary and the paste panel are counting the same endpoints differently"
    )
