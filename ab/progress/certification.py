"""Endpoint certification model (issue #69).

Separates **structural presence** from **actual certification**. The old report
conflated the two: a fixture file existing, a Markdown page existing, and an
AST reference to ``api.<group>.<method>()`` were all rendered as completion,
while only one endpoint in the repository had ever been verified to run.

Six distinct concepts, deliberately *not* collapsed into one score:

``IMPLEMENTED``
    A public SDK method with a :class:`~ab.api.route.Route`. Everything in the
    certification denominator is implemented by construction.
``STRUCTURALLY_COMPLETE``
    Implementation + canonical example + model/fixture test coverage + Sphinx
    page all present. **This is presence, not proof.**
``OPERATOR_READY``
    The canonical example references an approved shared constant (or needs no
    record identifier), so an operator has enough data to actually run it.
``LIVE_VERIFIED``
    Committed evidence shows the example completed successfully against a named
    environment, and that evidence is not stale.
``RESTORATION_VERIFIED``
    A mutating example is idempotent, or returned the record to its original
    state, with final-state verification recorded.
``CERTIFIED``
    Every *applicable* level above passes. Read-only endpoints do not need
    restoration; mutating ones do.

The pre-existing four-way harmony score is untouched and still means what it
always meant -- structural harmony. It is **not** redefined to imply live
certification; :func:`certification_summary` reports the two side by side so
the distinction stays visible in the artifact.

Staleness is **content-derived, never clock-derived**: evidence records the
SHA-256 of the fixture it was captured against, and goes stale when the
committed fixture no longer matches. A date-based rule would make the rendered
HTML change without a code change and thrash the no-drift gate.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
MOCKS_DIR = FIXTURES_DIR / "mocks"
MODEL_TESTS_DIR = REPO_ROOT / "tests" / "models"
EXAMPLES_CONSTANTS = REPO_ROOT / "examples" / "constants.py"
RUN_RESULTS = REPO_ROOT / "tests" / "example_run_results.json"


class CertLevel(str, Enum):
    """Certification ladder. Each level is reported independently."""

    IMPLEMENTED = "implemented"
    STRUCTURALLY_COMPLETE = "structurally_complete"
    OPERATOR_READY = "operator_ready"
    LIVE_VERIFIED = "live_verified"
    RESTORATION_VERIFIED = "restoration_verified"
    CERTIFIED = "certified"


class MutationClass(str, Enum):
    """How an example behaves against real data -- drives what evidence is required."""

    #: GET / no state change.
    READ_ONLY = "read_only"
    #: Mutating, but re-running leaves the same end state.
    IDEMPOTENT = "idempotent"
    #: Mutating; the example restores the original value before finishing.
    CIRCULAR_RESTORED = "circular_restored"
    #: Creates something and deletes it within the same run.
    DESTRUCTIVE_WITH_CLEANUP = "destructive_with_cleanup"
    #: Mutating; cleanup exists but an operator must perform it.
    MANUAL_CLEANUP = "manual_cleanup"
    #: Must never be automated (irreversible / customer-visible side effects).
    UNSAFE_FOR_AUTOMATION = "unsafe_for_automation"

    @property
    def is_mutating(self) -> bool:
        return self is not MutationClass.READ_ONLY

    @property
    def needs_restoration_evidence(self) -> bool:
        """Idempotent mutations are self-restoring; the rest must prove it."""
        return self in {
            MutationClass.CIRCULAR_RESTORED,
            MutationClass.DESTRUCTIVE_WITH_CLEANUP,
            MutationClass.MANUAL_CLEANUP,
        }


class EvidenceState(str, Enum):
    """Why an endpoint is or is not live-verified -- surfaced verbatim in the report."""

    #: Evidence present, fixture hash matches, status passing.
    FRESH = "fresh"
    #: Evidence present but recorded against a different fixture than the one on disk.
    STALE = "stale"
    #: Evidence present and explicitly failing.
    FAILING = "failing"
    #: No committed evidence at all.
    MISSING = "missing"
    #: Binary/no-content response: the call succeeded, JSON comparison skipped.
    #:
    #: This still requires committed evidence that the example *ran*. "Returns
    #: bytes" excuses the fixture diff, not the execution -- treating it as
    #: self-verifying would repeat the presence-as-proof mistake this module
    #: exists to correct.
    BINARY_VERIFIED = "binary_verified"


@dataclass(frozen=True)
class MutationEvidence:
    """Recorded proof that a mutating example ran and left the record correct."""

    record_identifier: str | None = None
    environment: str | None = None
    precondition: str | None = None
    mutation: str | None = None
    expected_result: str | None = None
    observed_result: str | None = None
    restoration: str | None = None
    final_state_verified: bool = False
    timestamp: str | None = None
    evidence_ref: str | None = None

    #: Fields that must be present for restoration to count as proven.
    _REQUIRED = (
        "record_identifier",
        "environment",
        "precondition",
        "mutation",
        "expected_result",
        "observed_result",
        "restoration",
        "timestamp",
    )

    @classmethod
    def from_dict(cls, raw: dict | None) -> "MutationEvidence | None":
        if not isinstance(raw, dict):
            return None
        return cls(
            record_identifier=raw.get("record_identifier"),
            environment=raw.get("environment"),
            precondition=raw.get("precondition"),
            mutation=raw.get("mutation"),
            expected_result=raw.get("expected_result"),
            observed_result=raw.get("observed_result"),
            restoration=raw.get("restoration"),
            final_state_verified=bool(raw.get("final_state_verified")),
            timestamp=raw.get("timestamp"),
            evidence_ref=raw.get("evidence_ref"),
        )

    def missing_fields(self) -> list[str]:
        return [f for f in self._REQUIRED if not getattr(self, f)]

    @property
    def is_complete(self) -> bool:
        """All required narrative fields present *and* final state re-checked."""
        return not self.missing_fields() and self.final_state_verified


@dataclass
class EndpointCertification:
    """Per-endpoint certification record. One row of the report."""

    endpoint_key: str
    http_method: str
    path: str
    response_model: str
    request_model: str | None = None

    # -- structural presence (never treated as proof of execution) --------
    has_example: bool = False
    has_fixture: bool = False
    has_model_test: bool = False
    has_sphinx: bool = False

    # -- operator readiness ------------------------------------------------
    shared_constants: tuple[str, ...] = ()
    needs_record_identifier: bool = True

    # -- live evidence -----------------------------------------------------
    evidence_state: EvidenceState = EvidenceState.MISSING
    mutation_class: MutationClass = MutationClass.READ_ONLY
    evidence: MutationEvidence | None = None
    evidence_detail: str | None = None
    example_path: str | None = None

    @property
    def implemented(self) -> bool:
        """True by construction -- the denominator is public methods with Routes."""
        return True

    @property
    def returns_no_content(self) -> bool:
        """True when the route declares no response model (HTTP 204).

        Such an endpoint has no response body, so a response fixture and a
        response-model test are not merely missing — there is nothing for them
        to contain. Requiring them made a 204 endpoint permanently
        uncertifiable. ``PATCH /job/{id}/timeline/{taskId}`` is one.
        """
        return not self.response_model

    @property
    def structurally_complete(self) -> bool:
        return (
            self.has_example
            and (self.returns_no_content or self.has_fixture)
            and (self.returns_no_content or self.has_model_test)
            and self.has_sphinx
        )

    @property
    def operator_ready(self) -> bool:
        """Enough approved data on hand to actually run the example."""
        if not self.has_example:
            return False
        if not self.needs_record_identifier:
            return True
        return bool(self.shared_constants)

    @property
    def live_verified(self) -> bool:
        return self.evidence_state in {
            EvidenceState.FRESH,
            EvidenceState.BINARY_VERIFIED,
        }

    @property
    def restoration_verified(self) -> bool:
        """Mutating endpoints must prove the record was left correct."""
        if not self.mutation_class.is_mutating:
            return True  # not applicable
        if self.mutation_class is MutationClass.UNSAFE_FOR_AUTOMATION:
            return False
        if self.mutation_class is MutationClass.IDEMPOTENT:
            return self.live_verified
        return bool(self.evidence and self.evidence.is_complete)

    @property
    def certified(self) -> bool:
        return (
            self.structurally_complete
            and self.operator_ready
            and self.live_verified
            and self.restoration_verified
        )

    def levels(self) -> list[CertLevel]:
        out = [CertLevel.IMPLEMENTED]
        if self.structurally_complete:
            out.append(CertLevel.STRUCTURALLY_COMPLETE)
        if self.operator_ready:
            out.append(CertLevel.OPERATOR_READY)
        if self.live_verified:
            out.append(CertLevel.LIVE_VERIFIED)
        if self.mutation_class.is_mutating and self.restoration_verified:
            out.append(CertLevel.RESTORATION_VERIFIED)
        if self.certified:
            out.append(CertLevel.CERTIFIED)
        return out

    def blockers(self) -> list[str]:
        """Human-readable reasons this endpoint is not certified."""
        out: list[str] = []
        if not self.has_example:
            out.append("no canonical example")
        if not self.returns_no_content and not self.has_fixture:
            out.append("no fixture")
        if not self.returns_no_content and not self.has_model_test:
            out.append("no model test")
        if not self.has_sphinx:
            out.append("no Sphinx page")
        if not self.operator_ready:
            out.append("no approved shared constant")
        if self.evidence_state is EvidenceState.MISSING:
            out.append("no run evidence")
        elif self.evidence_state is EvidenceState.STALE:
            out.append("run evidence stale (fixture changed since capture)")
        elif self.evidence_state is EvidenceState.FAILING:
            out.append("run evidence failing")
        if self.mutation_class.is_mutating and not self.restoration_verified:
            if self.mutation_class is MutationClass.UNSAFE_FOR_AUTOMATION:
                out.append("unsafe for automation")
            elif self.evidence and self.evidence.missing_fields():
                out.append(
                    "restoration evidence incomplete: "
                    + ", ".join(self.evidence.missing_fields())
                )
            else:
                out.append("no restoration evidence")
        return out


# ----------------------------------------------------------------------
# Signal collection
# ----------------------------------------------------------------------


def approved_constants() -> set[str]:
    """The shared ``examples/constants.py`` identifiers examples and tests agree on."""
    try:
        tree = ast.parse(EXAMPLES_CONSTANTS.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    out.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                out.add(node.target.id)
    return out


def _constants_used_by(example_path: Path, approved: set[str]) -> tuple[str, ...]:
    """Approved constants referenced by an example (static parse, no import)."""
    try:
        tree = ast.parse(example_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return ()
    used = {
        n.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in approved
    }
    return tuple(sorted(used))


def model_tested_names() -> set[str]:
    """Model class names referenced by ``tests/models/`` -- a real per-model signal.

    Replaces file-level ``coverage_pct > 0``, which marked every method in a
    module as tested if any test merely imported that module.
    """
    out: set[str] = set()
    if not MODEL_TESTS_DIR.is_dir():
        return out
    for path in MODEL_TESTS_DIR.rglob("test_*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "ab.api.models"
            ):
                out.update(a.name for a in node.names)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id and node.id[0].isupper():
                    out.add(node.id)
    return out


def fixture_sha256(model_name: str) -> str | None:
    """SHA-256 of the committed fixture for *model_name*, or ``None``."""
    for base in (FIXTURES_DIR, MOCKS_DIR):
        p = base / f"{model_name}.json"
        if p.is_file():
            return hashlib.sha256(p.read_bytes()).hexdigest()
    return None


def load_evidence() -> dict[str, dict]:
    """Committed run evidence, tolerating both schema 1 and schema 2."""
    if not RUN_RESULTS.is_file():
        return {}
    try:
        data = json.loads(RUN_RESULTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    results = data.get("results")
    return results if isinstance(results, dict) else {}


def classify_mutation(http_method: str, raw: dict | None) -> MutationClass:
    """Explicit ``mutation_class`` in evidence wins; otherwise infer from method."""
    if raw:
        declared = raw.get("mutation_class")
        if declared:
            try:
                return MutationClass(declared)
            except ValueError:
                pass
    if (http_method or "").upper() == "GET":
        return MutationClass.READ_ONLY
    return MutationClass.MANUAL_CLEANUP


def _evidence_state(
    raw: dict | None, model_name: str, http_method: str
) -> tuple[EvidenceState, str | None]:
    """Resolve evidence freshness by content hash, never by clock."""
    from ab.progress.models import is_binary_response

    binary = is_binary_response(model_name)
    if not raw:
        # Binary responses still need proof the call ran; only the diff is waived.
        return EvidenceState.MISSING, "binary response" if binary else None

    status = raw.get("status")
    if status == "failing":
        return EvidenceState.FAILING, raw.get("detail")
    if status not in {"passing", "binary"}:
        return EvidenceState.MISSING, f"recorded status {status!r}"

    if binary:
        return EvidenceState.BINARY_VERIFIED, "ran; JSON comparison not applicable"

    recorded = raw.get("fixture_sha256")
    if recorded:
        current = fixture_sha256(model_name)
        if current is None:
            return EvidenceState.STALE, "fixture referenced by evidence is gone"
        if current != recorded:
            return EvidenceState.STALE, "fixture changed since evidence was captured"
        return EvidenceState.FRESH, None

    # Schema-1 evidence predates hashing: usable, but cannot be proven current.
    return EvidenceState.STALE, "evidence predates fixture hashing (schema 1)"


def build_certification() -> list[EndpointCertification]:
    """Compute the certification record for every public discoverable endpoint."""
    from ab.api.rtd import endpoint_page_slug, endpoint_top_group
    from ab.cli.discovery import discover_endpoints_from_class
    from ab.progress.example_gen import strip_list_wrapper
    from ab.progress.example_index import build_example_index
    from ab.progress.scanner import scan_fixture_files

    index = build_example_index()
    fixtures = scan_fixture_files(FIXTURES_DIR)
    approved = approved_constants()
    tested = model_tested_names()
    evidence_all = load_evidence()

    out: list[EndpointCertification] = []
    for name, info in discover_endpoints_from_class().items():
        for m in info.methods:
            if m.route is None:
                continue
            key = f"api.{name}.{m.name}"
            model = strip_list_wrapper(m.route.response_model or "")
            ex = index.get(key)
            has_example = bool(ex and ex.is_canonical)

            example_path = ex.example_path if ex else None
            consts: tuple[str, ...] = ()
            if has_example and example_path:
                consts = _constants_used_by(REPO_ROOT / example_path, approved)

            raw = evidence_all.get(key)
            state, detail = _evidence_state(raw, model, m.route.method)

            top = endpoint_top_group(name)
            doc_rel = f"docs/api/{top}/{endpoint_page_slug(name, m.name)}.md"

            out.append(
                EndpointCertification(
                    endpoint_key=key,
                    http_method=m.route.method,
                    path=m.route.path,
                    response_model=model,
                    request_model=m.route.request_model,
                    has_example=has_example,
                    has_fixture=bool(model) and model in fixtures,
                    has_model_test=bool(model) and model in tested,
                    has_sphinx=(REPO_ROOT / doc_rel).is_file(),
                    shared_constants=consts,
                    needs_record_identifier="{" in (m.route.path or ""),
                    evidence_state=state,
                    mutation_class=classify_mutation(m.route.method, raw),
                    evidence=MutationEvidence.from_dict(
                        (raw or {}).get("evidence")
                    ),
                    evidence_detail=detail,
                    example_path=example_path,
                )
            )
    out.sort(key=lambda c: c.endpoint_key)
    return out


def certification_summary(rows: list[EndpointCertification]) -> dict[str, int]:
    """Headline counts. Structural and live figures are reported side by side."""
    return {
        "total": len(rows),
        "implemented": sum(1 for r in rows if r.implemented),
        "structurally_complete": sum(1 for r in rows if r.structurally_complete),
        "operator_ready": sum(1 for r in rows if r.operator_ready),
        "live_verified": sum(1 for r in rows if r.live_verified),
        "restoration_verified": sum(
            1 for r in rows if r.mutation_class.is_mutating and r.restoration_verified
        ),
        "certified": sum(1 for r in rows if r.certified),
        "evidence_missing": sum(
            1 for r in rows if r.evidence_state is EvidenceState.MISSING
        ),
        "evidence_stale": sum(
            1 for r in rows if r.evidence_state is EvidenceState.STALE
        ),
        "evidence_failing": sum(
            1 for r in rows if r.evidence_state is EvidenceState.FAILING
        ),
        "mutating": sum(1 for r in rows if r.mutation_class.is_mutating),
    }
