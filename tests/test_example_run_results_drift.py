"""Shape + no-drift guards for the run-results artifact (feature 037, T019).

Non-live. The committed ``tests/example_run_results.json`` (written by the live
harness / ingest) must conform to the contract and keep the report deterministic.
When the artifact is absent, the report derives statuses and these shape checks
skip — the no-drift guarantee still holds.
"""

from __future__ import annotations

import json

import pytest

from ab.progress.certification import MutationClass, MutationEvidence, fixture_sha256
from ab.progress.report import RUN_RESULTS_JSON, is_report_current, load_run_results

_PERSISTED_STATUSES = {"passing", "failing", "binary"}
_SOURCES = {"live", "paste", "binary"}
#: Schema 2 (issue #69) added environment, mutation_class, fixture_sha256 and the
#: mutation `evidence` block. Schema 1 entries still load, but carry no hash and
#: are therefore reported as stale rather than verified.
_SUPPORTED_SCHEMAS = {1, 2}


def test_run_results_shape_when_present() -> None:
    if not RUN_RESULTS_JSON.is_file():
        pytest.skip("no run-results artifact yet (operator runs scripts/run_examples.py)")

    data = json.loads(RUN_RESULTS_JSON.read_text(encoding="utf-8"))
    schema = data.get("schema")
    assert schema in _SUPPORTED_SCHEMAS, f"unsupported run-results schema {schema!r}"
    results = data["results"]
    assert isinstance(results, dict)

    # Keys must be sorted (no-drift stability).
    assert list(results) == sorted(results), "results keys must be sorted"

    for key, entry in results.items():
        assert key.startswith("api."), key
        assert entry["status"] in _PERSISTED_STATUSES, (key, entry["status"])
        assert entry["source"] in _SOURCES, (key, entry["source"])
        assert isinstance(entry["checked"], str) and len(entry["checked"]) == 10

        if schema < 2:
            continue

        assert entry.get("environment"), f"{key}: schema 2 requires an environment"
        mclass = entry.get("mutation_class")
        assert mclass in {m.value for m in MutationClass}, (key, mclass)

        sha = entry.get("fixture_sha256")
        if sha is not None:
            assert isinstance(sha, str) and len(sha) == 64, f"{key}: bad sha256"

        if MutationClass(mclass).needs_restoration_evidence:
            ev = MutationEvidence.from_dict(entry.get("evidence"))
            assert ev is not None, (
                f"{key}: mutation_class={mclass} requires an `evidence` block"
            )
            assert ev.is_complete, (
                f"{key}: incomplete restoration evidence — missing "
                f"{ev.missing_fields() or ['final_state_verified']}"
            )


def test_recorded_fixture_hashes_match_disk() -> None:
    """Committed evidence must reference the fixture actually shipped.

    This is what makes staleness content-derived: if a fixture is recaptured,
    its hash changes and the endpoint drops out of "live verified" until the
    evidence is refreshed.
    """
    if not RUN_RESULTS_JSON.is_file():
        pytest.skip("no run-results artifact yet")

    data = json.loads(RUN_RESULTS_JSON.read_text(encoding="utf-8"))
    for key, entry in data.get("results", {}).items():
        sha = entry.get("fixture_sha256")
        model = (entry.get("fixture") or "").removesuffix(".json")
        if not sha or not model:
            continue
        actual = fixture_sha256(model)
        assert actual is not None, f"{key}: fixture {model}.json referenced but absent"
        assert actual == sha, (
            f"{key}: fixture {model}.json changed since evidence was captured — "
            "re-run the example and refresh the evidence, or the report will "
            "correctly show it as stale"
        )


def test_loader_returns_dict() -> None:
    assert isinstance(load_run_results(), dict)


def test_report_is_current() -> None:
    """The committed report must match a fresh render (no-drift), artifact included."""
    assert is_report_current(), (
        "html/progress.html is stale — run `python scripts/generate_progress.py`"
    )
