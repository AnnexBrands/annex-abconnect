"""Repository-wide fixture safety gate (#70).

Committed fixtures are **sanitized structural evidence**, not raw API captures.
This is the gate that keeps it that way: it fails when a fixture carrying
obviously sensitive data is added.

Deterministic and offline. Runs in normal PR CI -- live endpoint execution
deliberately does not.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from ab.progress.fixture_audit import audit_repository, iter_fixture_files

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Values that must never reappear anywhere in the tree, fixture or not.
_FORBIDDEN = re.compile(r"@[\w-]+\.(?:com|co|org|net)\b")  # any email domain

#: Truncated SHA-256 of credentials that were once committed here. Stored as
#: digests, not literals: writing the secrets into a public test file to check
#: they are absent would republish them. They are rotated, but a rotated secret
#: is still a secret and this file does not need to know it.
_KNOWN_LEAKED_DIGESTS = frozenset(
    [
        "1fad617ef8de36cb",
        "5a53c90a9828254c",
        "71d75fe493504d48",
        "8d837ed443ee7449",
        "f5e0af00d712544f",
        "fbf914f0f9399d3d",
    ]
)


def _leaked_secret_in(text: str) -> list[str]:
    """Any previously-leaked credential present verbatim in *text*."""
    import hashlib

    found = []
    for token in re.findall(r"[A-Za-z0-9#*+/=_-]{8,40}", text):
        if hashlib.sha256(token.encode()).hexdigest()[:16] in _KNOWN_LEAKED_DIGESTS:
            found.append(token[:4] + "...")
    return found

#: Domains that are obviously synthetic. Everything else is treated as real
#: until proven otherwise -- the failure mode we care about is a production
#: address slipping in, not a fake one being over-reported.
_SYNTHETIC_DOMAINS = ("example.com", "test.com", "x.co", "example.org", "anthropic.com")

#: Files legitimately containing real addresses (author metadata, this test).
_ALLOWED_FILES = {
    "pyproject.toml",
    "tests/test_fixture_safety.py",
    ".claude/commands/commit.md",
    "CHANGELOG.md",
}


def test_no_fixture_contains_high_confidence_sensitive_data() -> None:
    """The core gate: no fixture may carry an unsanitized sensitive value."""
    result = audit_repository()
    unsafe = result.unsafe
    assert not unsafe, (
        f"{len(unsafe)} fixture(s) contain unsanitized sensitive values. "
        "Run: python scripts/audit_fixtures.py --apply\n  "
        + "\n  ".join(f"{f.path}: {f.kinds()}" for f in unsafe[:10])
    )


def test_fixture_scan_is_not_vacuous() -> None:
    """A broken scanner must not make the gate pass by finding nothing."""
    files = iter_fixture_files()
    assert len(files) > 100, f"only {len(files)} fixtures discovered — scan is blind"


def test_sanitization_is_idempotent_across_the_repository() -> None:
    """Re-sanitizing committed fixtures must be a no-op.

    If this fails, fixture hashes churn on every run, the no-drift gate thrashes
    and recorded certification evidence goes stale for no reason.
    """
    from ab.progress.fixture_audit import sanitize_repository

    changed = sanitize_repository(dry_run=True)
    assert not changed, (
        "sanitization is not a fixed point; these files would change again:\n  "
        + "\n  ".join(f"{rel} ({n} values)" for rel, n, _, _ in changed[:10])
    )


def test_no_production_contact_data_anywhere_in_the_tree() -> None:
    """Sensitive values must not hide outside fixtures either.

    The first audit found real addresses in spec markdown and a hard-coded
    production email inside a test assertion, neither of which a fixture-only
    scan would have caught.
    """
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.split()
    offenders: list[str] = []
    for rel in tracked:
        if rel in _ALLOWED_FILES or rel.startswith("html/"):
            continue
        path = REPO_ROOT / rel
        if not path.is_file() or path.suffix not in {".json", ".md", ".py", ".txt", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits = {
            m.group(0)
            for m in _FORBIDDEN.finditer(text)
            if not any(d in m.group(0).lower() for d in _SYNTHETIC_DOMAINS)
        }
        leaked = _leaked_secret_in(text)
        if hits or leaked:
            offenders.append(f"{rel}: {sorted(hits)[:3]}{' SECRET:' + str(leaked) if leaked else ''}")
    assert not offenders, "production contact data found outside fixtures:\n  " + "\n  ".join(
        offenders[:10]
    )


@pytest.mark.parametrize(
    "name,expected",
    [
        ("CountryCodeDto", "American Samoa"),
        ("DocumentTypeBySource", "Credit Card Auth"),
    ],
)
def test_reference_labels_are_not_sanitized(name: str, expected: str) -> None:
    """Lookup labels must survive sanitization.

    An early pass rewrote 69 of them ("American Samoa" -> "Emery Holt") because
    any two capitalised words looked like a person. Reference data that models
    validate against must stay readable.
    """
    import json

    path = REPO_ROOT / "tests" / "fixtures" / f"{name}.json"
    if not path.is_file():
        pytest.skip(f"{name} fixture not present")
    text = json.dumps(json.loads(path.read_text(encoding="utf-8")))
    assert expected in text, f"{expected!r} was sanitized out of {name}.json"
