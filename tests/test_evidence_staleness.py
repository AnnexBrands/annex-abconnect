"""Run evidence must go stale when the fixture it vouches for changes.

``fixture_sha256`` is what makes "live verified" mean something. It pins an
evidence entry to the exact fixture bytes that were verified, so editing a
fixture afterwards invalidates the claim instead of silently inheriting it.

Two ways to get this wrong, both asserted against here:

1. **Hashing the wrong thing.** The digest must come from the committed file's
   bytes, via the same function the verifier uses. Hashing the in-memory payload
   produces a different digest for identical content, and every endpoint reads
   as stale the moment it is verified.
2. **Recording it for failing runs.** A failing result's digest would pin
   evidence to a fixture that did not match, which reads as verification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ab.progress.certification import fixture_sha256

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
RUN_RESULTS = REPO_ROOT / "tests" / "example_run_results.json"


@pytest.fixture(scope="module")
def evidence() -> dict:
    return json.loads(RUN_RESULTS.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The digest identifies the committed file, not the payload
# ---------------------------------------------------------------------------


def test_digest_is_of_the_committed_file_bytes() -> None:
    name = "AddressIsValidResult"
    path = FIXTURES_DIR / f"{name}.json"
    assert fixture_sha256(name) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_digest_differs_from_hashing_the_parsed_payload() -> None:
    """The failure mode this pins down: re-serializing changes the bytes.

    ``json.dumps`` of the parsed fixture is semantically identical and textually
    different, so a verifier that hashed *that* would disagree with a verifier
    that hashed the file — and every entry would look stale forever.
    """
    name = "AddressIsValidResult"
    path = FIXTURES_DIR / f"{name}.json"
    reserialized = json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
    assert fixture_sha256(name) != hashlib.sha256(reserialized.encode()).hexdigest()


def test_digest_goes_stale_when_the_fixture_changes(tmp_path, monkeypatch) -> None:
    """Editing a fixture must invalidate evidence recorded against it."""
    from ab.progress import certification

    monkeypatch.setattr(certification, "FIXTURES_DIR", tmp_path)
    monkeypatch.setattr(certification, "MOCKS_DIR", tmp_path / "mocks")
    target = tmp_path / "Probe.json"

    target.write_text('{"a": 1}\n', encoding="utf-8")
    before = certification.fixture_sha256("Probe")

    target.write_text('{"a": 2}\n', encoding="utf-8")
    after = certification.fixture_sha256("Probe")

    assert before != after, "a changed fixture must produce a different digest"


def test_missing_fixture_has_no_digest(tmp_path, monkeypatch) -> None:
    from ab.progress import certification

    monkeypatch.setattr(certification, "FIXTURES_DIR", tmp_path)
    monkeypatch.setattr(certification, "MOCKS_DIR", tmp_path / "mocks")
    assert certification.fixture_sha256("NoSuchModel") is None


# ---------------------------------------------------------------------------
# The committed evidence file honours the contract
# ---------------------------------------------------------------------------


def test_every_passing_result_records_a_digest(evidence) -> None:
    missing = [
        key
        for key, e in evidence["results"].items()
        if e.get("status") == "passing" and e.get("fixture") and not e.get("fixture_sha256")
    ]
    assert not missing, f"passing results without fixture_sha256: {missing}"


def test_failing_results_do_not_record_a_digest(evidence) -> None:
    """A digest on a failing run would read as verification of a fixture that
    demonstrably did not match."""
    wrong = [
        key
        for key, e in evidence["results"].items()
        if e.get("status") == "failing" and e.get("fixture_sha256")
    ]
    assert not wrong, f"failing results must not claim a verified fixture: {wrong}"


def test_recorded_digests_match_the_fixtures_on_disk(evidence) -> None:
    """The refresh check: any fixture edited since its run shows up here.

    This is the gate that catches "someone changed a fixture and never re-ran
    the harness" — the evidence would otherwise keep asserting a verification
    that no longer holds.
    """
    stale = []
    for key, e in evidence["results"].items():
        recorded = e.get("fixture_sha256")
        if not recorded or not e.get("fixture"):
            continue
        current = fixture_sha256(e["fixture"].removesuffix(".json"))
        if current != recorded:
            stale.append(f"{key}: evidence {recorded[:12]}… vs disk {(current or 'missing')[:12]}…")
    assert not stale, (
        "fixtures changed since their run was recorded — re-run "
        "`python scripts/run_examples.py`:\n  " + "\n  ".join(stale)
    )


def test_digests_are_well_formed(evidence) -> None:
    for key, e in evidence["results"].items():
        d = e.get("fixture_sha256")
        if d is not None:
            assert isinstance(d, str) and len(d) == 64, f"{key}: malformed digest {d!r}"
