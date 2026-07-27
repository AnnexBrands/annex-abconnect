"""The example capture path must not be able to leak live data (issue #70).

Examples are run against live staging. Before this gate existed, ``save()``
defaulted to ``tests/fixtures/``, so an ordinary ``python -m examples.companies``
overwrote committed fixtures with the raw response — which put 21 carrier
secrets and several thousand real UUIDs, emails and addresses into the working
tree of a public repository.

Two properties close that hole, and both are asserted here:

1. the committed fixture tree is not a reachable destination from ``save()``;
2. nothing reaches disk unsanitized, and anything the sanitizer cannot classify
   blocks the write rather than being written verbatim.

These are deliberately black-box: they assert on the *bytes on disk*, not on
which helper was called, so a future capture helper that forgets to sanitize
still fails.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from examples import _capture
from examples._capture import UnsafeCaptureTarget, capture_dir, save

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

#: A response with one of everything the sanitizer is supposed to catch.
LIVE_RESPONSE = {
    "companyName": "Lefflers Antiques",
    "contactEmail": "dana.whitfield@lefflers.com",
    "phone": "619-555-0134",
    "addressLine1": "7580 Metropolitan Dr",
    "city": "San Diego",
    "postalCode": "92108",
    "latitude": 32.7776075,
    "longitude": -117.1587817,
    "companyId": "daf9b34b-ce6a-4f2f-9207-15278c06b7d2",
    "accountInformation": {
        "clientSecret": "s3cr3t-carrier-key",
        "accessKey": "AKIAIOSFODNN7EXAMPLE",
        "shipperNumber": "0000123456",
    },
    "isActive": True,
    "status": "Active",
}

_SECRETS = ("s3cr3t-carrier-key", "AKIAIOSFODNN7EXAMPLE")
_PII = (
    "dana.whitfield@lefflers.com",
    "619-555-0134",
    "7580 Metropolitan Dr",
    "daf9b34b-ce6a-4f2f-9207-15278c06b7d2",
)


# ---------------------------------------------------------------------------
# The committed fixture tree is unreachable
# ---------------------------------------------------------------------------


def test_default_capture_destination_is_not_the_committed_tree() -> None:
    assert capture_dir() != FIXTURES_DIR
    assert FIXTURES_DIR not in capture_dir().parents
    assert capture_dir() == _capture.CAPTURES_DIR


def test_redirecting_captures_into_the_fixture_tree_is_refused(monkeypatch) -> None:
    """Even an explicit override cannot aim a capture at a committed fixture."""
    monkeypatch.setenv(_capture.CAPTURE_DIR_ENV, str(FIXTURES_DIR))
    with pytest.raises(UnsafeCaptureTarget):
        capture_dir()
    with pytest.raises(UnsafeCaptureTarget):
        save("CompanyDetails.json", LIVE_RESPONSE)


def test_redirecting_into_a_fixture_subdirectory_is_refused(monkeypatch) -> None:
    monkeypatch.setenv(_capture.CAPTURE_DIR_ENV, str(FIXTURES_DIR / "requests"))
    with pytest.raises(UnsafeCaptureTarget):
        capture_dir()


def test_a_live_capture_leaves_the_fixture_tree_byte_identical(tmp_path, monkeypatch) -> None:
    """Acceptance: an ordinary example run does not modify committed fixtures."""
    before = {
        p.relative_to(FIXTURES_DIR).as_posix(): p.read_bytes()
        for p in FIXTURES_DIR.rglob("*.json")
    }
    monkeypatch.setenv(_capture.CAPTURE_DIR_ENV, str(tmp_path))
    save("CompanyDetails.json", LIVE_RESPONSE)
    save("Job.json", [LIVE_RESPONSE, LIVE_RESPONSE])
    after = {
        p.relative_to(FIXTURES_DIR).as_posix(): p.read_bytes()
        for p in FIXTURES_DIR.rglob("*.json")
    }
    assert before == after


# ---------------------------------------------------------------------------
# Nothing reaches disk unsanitized
# ---------------------------------------------------------------------------


def _capture_to(tmp_path, monkeypatch, payload, name="CompanyDetails.json") -> Path | None:
    monkeypatch.setenv(_capture.CAPTURE_DIR_ENV, str(tmp_path))
    return save(name, payload)


def test_secrets_never_reach_disk(tmp_path, monkeypatch) -> None:
    _capture_to(tmp_path, monkeypatch, LIVE_RESPONSE)
    written = "\n".join(
        p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file()
    )
    for secret in _SECRETS:
        assert secret not in written, f"secret {secret!r} written to disk"


def test_pii_never_reaches_disk(tmp_path, monkeypatch) -> None:
    _capture_to(tmp_path, monkeypatch, LIVE_RESPONSE)
    written = "\n".join(
        p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file()
    )
    for value in _PII:
        assert value not in written, f"PII {value!r} written to disk"


def test_capture_keeps_structure_while_replacing_values(tmp_path, monkeypatch) -> None:
    """Sanitizing must not cost the fixture its shape — that is what it is for."""
    out = _capture_to(tmp_path, monkeypatch, LIVE_RESPONSE)
    assert out is not None
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == set(LIVE_RESPONSE)
    assert data["isActive"] is True
    assert data["status"] == "Active"  # structural enum survives
    assert data["contactEmail"] != LIVE_RESPONSE["contactEmail"]
    assert re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", data["contactEmail"])


def test_capture_is_deterministic(tmp_path, monkeypatch) -> None:
    """Re-capturing an unchanged response must be byte-identical, or the
    no-drift gates would thrash on phantom diffs."""
    a = _capture_to(tmp_path / "a", monkeypatch, LIVE_RESPONSE)
    b = _capture_to(tmp_path / "b", monkeypatch, LIVE_RESPONSE)
    assert a is not None and b is not None
    assert a.read_bytes() == b.read_bytes()


def test_review_tier_blocks_the_write_and_leaves_a_note(tmp_path, monkeypatch) -> None:
    """A value the sanitizer cannot classify is left verbatim, so it must not
    be written under a name implying it was cleaned."""
    payload = {"name": "Dana Whitfield", "isValid": True}
    out = _capture_to(tmp_path, monkeypatch, payload)

    assert out is None, "capture with REVIEW findings must not write a fixture"
    assert not (tmp_path / "CompanyDetails.json").exists()

    notes = list(tmp_path.glob("*.review.txt"))
    assert notes, "a review artifact must be produced"
    text = notes[0].read_text(encoding="utf-8")
    assert "name" in text
    assert "approve_fixture" in text, "the note must point at the approval path"


def test_review_note_does_not_itself_become_a_fixture(tmp_path, monkeypatch) -> None:
    _capture_to(tmp_path, monkeypatch, {"name": "Dana Whitfield"})
    assert not list(tmp_path.glob("*.json"))


# ---------------------------------------------------------------------------
# End-to-end: the real example modules
# ---------------------------------------------------------------------------


def test_no_example_module_writes_to_the_fixture_tree() -> None:
    """No example may build a path into the committed tree and write to it.

    A grep, not a live run: this must hold without credentials and without
    touching staging. Writes elsewhere are fine — ``examples/documents.py``
    legitimately writes a throwaway PDF to /tmp to exercise an upload — so this
    looks for the *destination*, not for the act of writing.
    """
    offenders: list[str] = []
    for path in (REPO_ROOT / "examples").rglob("*.py"):
        if path.name == "_capture.py":
            continue
        rel = path.relative_to(REPO_ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"FIXTURES_DIR|REQUESTS_DIR|tests/fixtures", line) and re.search(
                r"write_text|write_bytes|json\.dump|open\s*\(", line
            ):
                offenders.append(f"{rel}:{lineno}: {line.strip()[:80]}")
    assert not offenders, "examples must persist through _capture.save():\n  " + "\n  ".join(
        offenders
    )


def test_legacy_runner_persists_through_the_shared_capture_path() -> None:
    """``_runner.py`` is deprecated but still imported by many ``_*.py``
    examples, so it must not keep its own write path."""
    text = (REPO_ROOT / "examples" / "_runner.py").read_text(encoding="utf-8")
    assert "from examples._capture import save" in text
    assert "FIXTURES_DIR / entry.fixture_file" not in text


def test_harness_dry_run_touches_no_fixture() -> None:
    """``--list`` plans the sweep without network or writes."""
    before = {p: p.read_bytes() for p in FIXTURES_DIR.rglob("*.json")}
    subprocess.run(
        ["python", "scripts/run_examples.py", "--list"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        check=True,
    )
    assert {p: p.read_bytes() for p in FIXTURES_DIR.rglob("*.json")} == before
