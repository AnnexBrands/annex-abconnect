"""Shared capture helper for canonical examples.

Every canonical (plain-script) example imports :func:`save` to persist the response
it just printed. This replaces each example's bespoke ``_save`` and adds the one
piece of magic the run-and-verify harness depends on: **destination redirection**.

- Normal use (an operator running ``python -m examples dashboard``): ``save`` writes
  to the scratch tree ``tests/captures/<name>``.
- Harness use (``scripts/run_examples.py``): the harness sets
  ``AB_EXAMPLE_CAPTURE_DIR`` before running the example in a subprocess; ``save``
  then writes to that directory instead.

Two invariants hold on every path through this module:

1. **Nothing is written unsanitized.** Every payload goes through
   ``ab.progress.sanitize`` first, and a capture carrying values the sanitizer
   could not classify (its REVIEW tier) is refused outright — those values are
   left verbatim by design, so writing them would persist real data under a
   name implying it had been cleaned. A ``.review.txt`` note is produced instead.
2. **The committed fixture tree is never a destination.** ``tests/fixtures/`` is
   read-only from here, whatever ``AB_EXAMPLE_CAPTURE_DIR`` says. Fixtures are
   updated through one path only: the workbench's ``propose_fixture()`` ->
   operator review -> ``approve_fixture(confirm=True, accept_review=...)``.

Serialization is byte-identical to ``examples/dashboard.py``'s original ``_save`` and
to ``ab.cli.formatter.format_result`` (``model_dump(by_alias=True, mode="json")``),
so a re-capture or an ingested paste produces the same bytes a prior capture did.

See ``specs/037-example-coverage/contracts/example-contract.md`` §2.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

#: Environment variable the harness sets to redirect captures to a temp dir.
CAPTURE_DIR_ENV = "AB_EXAMPLE_CAPTURE_DIR"

_REPO_ROOT = Path(__file__).resolve().parent.parent

#: The committed fixture tree. **Never written through this module** — see
#: :func:`capture_dir`. Read-only here; it is the comparison baseline.
FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures"
#: Request fixtures (bodies / params) live here.
REQUESTS_DIR = FIXTURES_DIR / "requests"
#: Default destination for example captures: a scratch tree, git-ignored.
CAPTURES_DIR = _REPO_ROOT / "tests" / "captures"


def load_request(name: str) -> dict:
    """Load a request fixture (body or params) from ``tests/fixtures/requests/``.

    Lets a plain example demonstrate a POST/param call with the same real request
    data the operator captured, e.g. ``api.address.validate(**load_request(
    "AddressValidateParams.json"))``.
    """
    return json.loads((REQUESTS_DIR / name).read_text(encoding="utf-8"))


class UnsafeCaptureTarget(RuntimeError):
    """Raised when a capture would land in the committed fixture tree."""


def _is_within(target: Path, parent: Path) -> bool:
    try:
        target.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def capture_dir() -> Path:
    """Return the directory ``save`` writes to — never the committed tree.

    ``AB_EXAMPLE_CAPTURE_DIR`` when set (harness verify mode), else
    ``tests/captures/``.

    Running an example is how a live response is *observed*, not how a fixture
    is *approved*. Defaulting this to ``tests/fixtures/`` meant an ordinary
    ``python -m examples.companies`` overwrote committed fixtures with raw live
    data — that is how 21 carrier secrets and several thousand real UUIDs,
    emails and addresses once landed in the working tree of a public repo.
    Committed fixtures are now updated through exactly one path: the workbench's
    ``propose_fixture()`` -> operator review -> ``approve_fixture()``.
    """
    override = os.environ.get(CAPTURE_DIR_ENV)
    target = Path(override) if override else CAPTURES_DIR
    if _is_within(target, FIXTURES_DIR):
        raise UnsafeCaptureTarget(
            f"refusing to capture into the committed fixture tree ({target}). "
            "Examples observe live responses; fixtures are updated only through "
            "the workbench: propose_fixture() -> review -> approve_fixture()."
        )
    return target


#: Env var an operator sets to opt INTO running state-mutating example calls.
RUN_MUTATIONS_ENV = "AB_RUN_MUTATIONS"

#: Set by ``scripts/run_examples.py``: this capture exists only to be compared
#: and then thrown away, never to become a fixture.
VERIFY_MODE_ENV = "AB_EXAMPLE_VERIFY"

#: What a REVIEW-tier string becomes in a verify capture.
REVIEW_PLACEHOLDER = "REVIEW-REDACTED"


def verify_mode() -> bool:
    """True when the harness is capturing purely to compare structure."""
    return os.environ.get(VERIFY_MODE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _placeholder(value: Any) -> Any:
    """A stand-in of the same JSON type, carrying none of the original."""
    if isinstance(value, str):
        return REVIEW_PLACEHOLDER
    if isinstance(value, float):
        return 0.0
    if isinstance(value, int):
        return 0
    return None


def redact(node: Any, originals: list[Any]) -> Any:
    """Replace every occurrence of a REVIEW-flagged value with a placeholder.

    Matching is by value rather than by path, so a value flagged once is redacted
    everywhere it appears. That over-redacts in principle -- an unrelated field
    holding the same string loses it too -- which is the safe direction, and
    costs nothing: the comparator reads types and structure, never values.
    """
    if isinstance(node, dict):
        return {k: redact(v, originals) for k, v in node.items()}
    if isinstance(node, list):
        return [redact(v, originals) for v in node]
    if node is None or isinstance(node, bool):
        return node
    for original in originals:
        if type(node) is type(original) and node == original:
            return _placeholder(node)
    return node


def mutations_enabled() -> bool:
    """True only when the operator explicitly opts into mutating calls.

    Examples wrap create/update/delete (and other state-writing) calls in
    ``if mutations_enabled():`` so a default run — and the verify harness, which
    never sets this — exercises only the safe read-only calls. Set
    ``AB_RUN_MUTATIONS=1`` to run them deliberately.
    """
    return os.environ.get(RUN_MUTATIONS_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def to_jsonable(payload: Any) -> Any:
    """Convert *payload* to the JSON shape fixtures are stored in.

    - ``BaseModel``        -> ``model_dump(by_alias=True, mode="json")``
    - ``list``             -> element-wise (models dumped, others passed through)
    - other JSON-able      -> returned as-is
    """
    from pydantic import BaseModel

    if isinstance(payload, list):
        return [
            item.model_dump(by_alias=True, mode="json")
            if isinstance(item, BaseModel)
            else item
            for item in payload
        ]
    if isinstance(payload, BaseModel):
        return payload.model_dump(by_alias=True, mode="json")
    return payload


def save(name: str, payload: Any) -> Path | None:
    """Serialize *payload* and write it to ``<capture_dir>/<name>``.

    Binary (``bytes``) payloads are never written (they cannot be a JSON fixture);
    a note is printed and ``None`` is returned (supports the ``binary`` run status).

    Returns the path written, or ``None`` for binary/skipped payloads.
    """
    if isinstance(payload, bytes):
        print(f"  (binary response, {len(payload)} bytes — fixture save skipped)")
        return None

    # An empty live result (no data on the test account) must NOT overwrite a
    # committed fixture that may hold real captured rows.
    if isinstance(payload, list) and not payload:
        print(f"  (empty list — not overwriting {capture_dir() / name})")
        return None

    from ab.progress.sanitize import sanitize

    data = to_jsonable(payload)
    out = capture_dir() / name

    # Sanitize before the payload ever reaches disk. Deterministic, so an
    # unchanged response re-captures byte-identically, and it is also what makes
    # the capture comparable to the (also sanitized) committed fixture.
    sanitized, report = sanitize(data)

    if report.needs_review:
        # REVIEW findings are values the sanitizer could not classify from
        # context and therefore left *verbatim*. They never reach disk here.
        review = out.with_suffix(out.suffix + ".review.txt")
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text(
            f"{len(report.review)} value(s) could not be classified.\n"
            f"To turn this capture into a committed fixture, resolve them through the\n"
            f"workbench, which records an operator decision:\n"
            f"    s.propose_fixture(); s.approve_fixture(confirm=True, accept_review=True)\n\n"
            + "\n".join(d.render() for d in report.review)
            + "\n",
            encoding="utf-8",
        )

        if not verify_mode():
            # Capture mode: fail closed. Writing these would persist real data
            # under a name implying it had been cleaned.
            print(
                f"  BLOCKED: {len(report.review)} value(s) need review — no fixture written.\n"
                f"  review notes -> {review}"
            )
            return None

        # Verify mode: the harness compares structure and discards the file, and
        # free text (an error message, a note, a description) is flagged on most
        # responses -- failing closed here would leave the sweep unable to check
        # anything rather than making it safer. Redact to a same-typed
        # placeholder: the unclassified value still never reaches disk, and shape
        # -- all the comparator reads -- survives.
        sanitized = redact(sanitized, [d.original for d in report.review])
        print(f"  ({len(report.review)} unclassified value(s) redacted for comparison)")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    note = f" ({report.changed_count} value(s) sanitized)" if report.was_sanitized else ""
    print(f"  saved -> {out}{note}")
    return out
