"""Certification session: the workflow the notebook drives (issue #71).

One :class:`CertificationSession` per endpoint. Every step the operator performs
in the notebook is a method here, so pytest exercises the *same* code path --
notebook cells hold no logic of their own and cannot drift from the tests.

The session is deliberately explicit about consent. Nothing is executed against
a mutating endpoint until :meth:`classify` records how it behaves, and nothing
is written to ``tests/fixtures/`` until :meth:`approve_fixture` is called with a
sanitized payload the operator has seen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ab.progress.certification import MutationClass, MutationEvidence
from ab.progress.certification import fixture_sha256 as committed_fixture_sha256
from ab.progress.certify.summarize import ResponseSummary, summarize
from ab.progress.sanitize import SanitizeReport, sanitize

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
REQUESTS_DIR = FIXTURES_DIR / "requests"
RUN_RESULTS = REPO_ROOT / "tests" / "example_run_results.json"


# ----------------------------------------------------------------------
# Check results
# ----------------------------------------------------------------------


@dataclass
class Check:
    """One green/red line in the notebook's result panel."""

    name: str
    passed: bool | None  # None = not applicable / not run
    detail: str = ""

    @property
    def symbol(self) -> str:
        return "—" if self.passed is None else ("✅" if self.passed else "❌")

    def render(self) -> str:
        tail = f"  {self.detail}" if self.detail else ""
        return f"{self.symbol} {self.name}{tail}"


@dataclass
class CheckReport:
    """The green/red panel (workflow step 12)."""

    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, passed: bool | None, detail: str = "") -> None:
        self.checks = [c for c in self.checks if c.name != name]
        self.checks.append(Check(name, passed, detail))

    def get(self, name: str) -> Check | None:
        return next((c for c in self.checks if c.name == name), None)

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.passed is False]

    @property
    def all_green(self) -> bool:
        return not self.failed

    def render(self) -> str:
        order = [
            "request-model validation",
            "expected negative test",
            "endpoint execution",
            "response-model validation",
            "undeclared response fields",
            "fixture match",
            "restoration",
        ]
        rank = {n: i for i, n in enumerate(order)}
        rows = sorted(self.checks, key=lambda c: rank.get(c.name, 99))
        return "\n".join(c.render() for c in rows)

    def _repr_pretty_(self, p, cycle):  # pragma: no cover - notebook hook
        p.text(self.render())

    def __repr__(self) -> str:
        return self.render()


# ----------------------------------------------------------------------
# Discovery / resolution
# ----------------------------------------------------------------------


def list_endpoints(filter_text: str = "") -> list[str]:
    """The 218 public SDK methods, optionally filtered (workflow step 1)."""
    from ab.progress.inventory import public_endpoint_keys

    keys = public_endpoint_keys()
    if filter_text:
        needle = filter_text.lower()
        keys = tuple(k for k in keys if needle in k.lower())
    return list(keys)


def resolve_route(endpoint_key: str):
    """Return the live ``Route`` for ``api.<group>.<method>``."""
    from ab.cli.discovery import discover_endpoints_from_class

    if not endpoint_key.startswith("api."):
        raise ValueError(f"endpoint key must start with 'api.': {endpoint_key!r}")
    group, method_name = endpoint_key[len("api.") :].rsplit(".", 1)
    info = discover_endpoints_from_class().get(group)
    if info is None:
        raise KeyError(f"unknown endpoint group {group!r}")
    for m in info.methods:
        if m.name == method_name and m.route is not None:
            return m.route
    raise KeyError(f"unknown routed method {endpoint_key!r}")


def resolve_model(name: str | None):
    """Resolve a model name to its class (request, params, or response)."""
    if not name:
        return None
    import ab.api.models as models_pkg
    from ab.progress.example_gen import strip_list_wrapper

    return getattr(models_pkg, strip_list_wrapper(name), None)


def approved_constants() -> dict[str, Any]:
    """The shared constants examples and tests agree on (workflow step 2)."""
    import examples.constants as c

    return {
        n: getattr(c, n)
        for n in dir(c)
        if n.isupper() and not n.startswith("_")
    }


def load_request_fixture(name: str) -> dict | None:
    """Load a request fixture from ``tests/fixtures/requests/`` (step 3)."""
    path = REQUESTS_DIR / (name if name.endswith(".json") else f"{name}.json")
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_response_fixture(model_name: str) -> Any | None:
    """Load the committed response fixture for a model, if any."""
    for base in (FIXTURES_DIR, FIXTURES_DIR / "mocks"):
        path = base / f"{model_name}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def compare_to_fixture(payload: Any, fixture: Any, *, model: Any = None) -> tuple[bool, list[str]]:
    """Structural comparison against the committed fixture (step 11).

    Delegates to :func:`ab.progress.compare.compare`, the same implementation
    ``scripts/run_examples.py`` uses, so the notebook and the harness cannot
    disagree about whether an endpoint matches. Compares shape and JSON value
    types -- never values, because the committed fixture is sanitized and its
    values deliberately differ from live.
    """
    from ab.progress.compare import compare as compare_structure

    report = compare_structure(payload, fixture, model=model)
    lines = [d.render() for d in report.diffs]
    lines += [f"+ {e}: undeclared field on the response model" for e in report.extras]
    return report.ok, lines


# ----------------------------------------------------------------------
# Session
# ----------------------------------------------------------------------


class MutationNotClassified(RuntimeError):
    """Raised when a mutating endpoint is executed before classification."""


@dataclass
class CertificationSession:
    """Drives one endpoint through the certification workflow."""

    endpoint_key: str
    environment: str = "staging"

    route: Any = field(init=False, default=None)
    mutation_class: MutationClass | None = field(init=False, default=None)
    checks: CheckReport = field(init=False, default_factory=CheckReport)

    request_payload: dict | None = field(init=False, default=None)
    call_kwargs: dict | None = field(init=False, default=None)
    request_instance: Any = field(init=False, default=None)
    response_model: Any = field(init=False, default=None)
    response_payload: Any = field(init=False, default=None)
    summary: ResponseSummary | None = field(init=False, default=None)
    sanitized: Any = field(init=False, default=None)
    sanitize_report: SanitizeReport | None = field(init=False, default=None)
    evidence: MutationEvidence | None = field(init=False, default=None)
    fixture_saved: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.route = resolve_route(self.endpoint_key)
        if (self.route.method or "").upper() == "GET":
            self.mutation_class = MutationClass.READ_ONLY

    # -- models ---------------------------------------------------------

    @property
    def response_model_name(self) -> str:
        from ab.progress.example_gen import strip_list_wrapper

        return strip_list_wrapper(self.route.response_model or "")

    def request_model(self):
        """The request-body or params model for this endpoint (step 5)."""
        return resolve_model(self.route.request_model) or resolve_model(
            self.route.params_model
        )

    def validate_request(self, data: dict, model: Any = None) -> Any:
        """Cast raw request data into the endpoint's model (steps 4-6).

        Populates two different views, because they are genuinely different:

        * :attr:`request_payload` -- aliased, what goes over the wire
          (``{"Line1": ...}``), which is what step 6 displays;
        * :attr:`call_kwargs` -- snake_case field names, what the SDK method
          signature actually accepts (``validate(line1=...)``).

        Request fixtures are stored in wire form, so passing them straight to a
        bound SDK method raises ``TypeError: unexpected keyword argument
        'Line1'``. Resolving that here means every endpoint gets it right rather
        than each notebook cell hand-mapping aliases.

        *model* names the concrete request class for endpoints whose body is
        polymorphic. ``POST /job/{id}/timeline`` is one: the body varies by
        ``taskCode`` (``SimpleTaskRequest``, ``CarrierTaskRequest``, ...), so the
        route deliberately declares no ``request_model`` and the operator picks
        the one they are certifying. Without this the session fell back to the
        route's *query-params* model and rejected a valid body.
        """
        model_cls = model or self.request_model()
        if model_cls is None:
            self.request_payload = dict(data)
            self.call_kwargs = dict(data)
            self.checks.add(
                "request-model validation", None, "endpoint takes plain kwargs"
            )
            return None
        instance = model_cls.model_validate(data)
        self.request_instance = instance
        self.request_payload = instance.model_dump(by_alias=True, mode="json")
        self.call_kwargs = instance.model_dump(
            by_alias=False, mode="json", exclude_none=True
        )
        self.checks.add(
            "request-model validation", True, f"{model_cls.__name__} accepted"
        )
        return instance

    def expect_validation_error(self, data: dict, *, omit: str) -> str:
        """Confirm omitting a required field is rejected (step 7).

        Returns the rendered error. Records a **failed** check if the model
        wrongly accepts the payload -- a required field that is not enforced is
        a real defect in the model.
        """
        from pydantic import ValidationError

        model_cls = self.request_model()
        if model_cls is None:
            self.checks.add("expected negative test", None, "no request model")
            return "no request model for this endpoint"

        broken = {k: v for k, v in data.items() if k != omit}
        try:
            model_cls.model_validate(broken)
        except ValidationError as exc:
            self.checks.add(
                "expected negative test", True, f"omitting {omit!r} correctly rejected"
            )
            return str(exc)

        # No error. Distinguish "this model enforces nothing" from "this one
        # field is wrongly optional" — only the latter is a model defect.
        required = self.required_fields()
        if not required:
            self.checks.add(
                "expected negative test",
                None,
                f"{model_cls.__name__} declares no required fields — nothing to omit",
            )
            return (
                f"{model_cls.__name__} has no required fields; every field is "
                "Optional, so omitting one cannot raise. Not a failure, but this "
                "model enforces nothing at the boundary."
            )
        self.checks.add(
            "expected negative test",
            False,
            f"omitting {omit!r} was accepted — required fields are {required}",
        )
        return f"NO ERROR: {model_cls.__name__} accepted a payload missing {omit!r}"

    def bind_arguments(self, call) -> dict:
        """Adapt the validated request to *call*'s actual signature.

        The SDK uses two calling conventions and the operator should not have to
        remember which applies to a given endpoint:

        * body endpoints take the model itself -- ``search(data=...)``;
        * query/path endpoints take exploded snake_case kwargs --
          ``validate(line1=..., city=...)``.

        Passing the wrong one raises ``TypeError: unexpected keyword argument``,
        which across 218 endpoints would be a per-endpoint papercut.
        """
        import inspect

        if self.call_kwargs is None:
            return {}
        try:
            params = inspect.signature(call).parameters
        except (TypeError, ValueError):
            return dict(self.call_kwargs)

        for body_param in ("data", "body", "payload", "request"):
            if body_param in params:
                return {body_param: self.request_instance or self.call_kwargs}

        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
            return dict(self.call_kwargs)
        return {k: v for k, v in self.call_kwargs.items() if k in params}

    def required_fields(self) -> list[str]:
        """Required field names on the request model — what is safe to omit."""
        model_cls = self.request_model()
        if model_cls is None:
            return []
        return [n for n, f in model_cls.model_fields.items() if f.is_required()]

    # -- mutation consent ------------------------------------------------

    def classify(self, mutation_class: str | MutationClass) -> MutationClass:
        """Record how this endpoint behaves before it may be executed."""
        self.mutation_class = MutationClass(
            mutation_class.value
            if isinstance(mutation_class, MutationClass)
            else mutation_class
        )
        return self.mutation_class

    def _require_classification(self) -> None:
        if self.mutation_class is None:
            raise MutationNotClassified(
                f"{self.endpoint_key} is {self.route.method}; call "
                "session.classify(...) with a MutationClass before executing"
            )
        if self.mutation_class is MutationClass.UNSAFE_FOR_AUTOMATION:
            raise MutationNotClassified(
                f"{self.endpoint_key} is classified unsafe_for_automation "
                "and must not be executed by the workbench"
            )

    # -- execution -------------------------------------------------------

    def execute(self, call, *args, **kwargs) -> Any:
        """Invoke the endpoint (step 8). *call* is the bound SDK method.

        The caller supplies the bound method so the session never has to guess
        argument shapes; mutation consent is still enforced here.

        Called with no arguments, the request validated by
        :meth:`validate_request` is adapted to the method's own signature via
        :meth:`bind_arguments`.
        """
        self._require_classification()
        if not args and not kwargs and self.request_payload is not None:
            kwargs = self.bind_arguments(call)
        try:
            result = call(*args, **kwargs)
        except Exception as exc:  # surfaced as a red check, not a traceback
            self.checks.add("endpoint execution", False, f"{type(exc).__name__}: {exc}")
            raise
        self.checks.add("endpoint execution", True, f"{self.route.method} {self.route.path}")
        return self.record_response(result)

    def record_response(self, result: Any) -> Any:
        """Validate, summarize and check a response (steps 9-12)."""
        self.response_model = result
        if hasattr(result, "model_dump"):
            self.response_payload = result.model_dump(by_alias=True, mode="json")
            self.checks.add(
                "response-model validation", True, type(result).__name__
            )
        elif isinstance(result, list) and any(hasattr(i, "model_dump") for i in result):
            # A List[...] route: dump element-wise. Without this the payload
            # stays a list of model *objects*, which is not JSON-able, and
            # approve_fixture() fails at the last step of the workflow.
            self.response_payload = [
                item.model_dump(by_alias=True, mode="json")
                if hasattr(item, "model_dump")
                else item
                for item in result
            ]
            element = next(type(i).__name__ for i in result if hasattr(i, "model_dump"))
            self.checks.add(
                "response-model validation", True, f"List[{element}] ({len(result)} items)"
            )
        else:
            self.response_payload = result
            self.checks.add(
                "response-model validation", None, f"untyped {type(result).__name__}"
            )

        self.summary = summarize(result, self.response_payload)
        extras = self.summary.extras
        self.checks.add(
            "undeclared response fields",
            not extras,
            "none" if not extras else f"{len(extras)}: {', '.join(list(extras)[:5])}",
        )

        fixture = load_response_fixture(self.response_model_name)
        if fixture is None:
            self.checks.add("fixture match", None, "no committed fixture yet")
        else:
            ok, diffs = compare_to_fixture(self.response_payload, fixture)
            self.checks.add(
                "fixture match",
                ok,
                "structure matches" if ok else f"{len(diffs)} shape differences",
            )
        return self.summary

    # -- sanitization ----------------------------------------------------

    def propose_fixture(self) -> SanitizeReport:
        """Sanitize the live response and return the diff for review (step 13)."""
        if self.response_payload is None:
            raise RuntimeError("no response recorded yet")
        self.sanitized, self.sanitize_report = sanitize(self.response_payload)
        return self.sanitize_report

    def approve_fixture(self, *, confirm: bool = False, accept_review: bool = False) -> Path:
        """Write the sanitized fixture. Requires explicit operator approval.

        The sanitizer rewrites only what it is confident about. Anything it
        cannot decide from context -- a bare ``name`` that may be a person or
        may be a lookup label -- is reported as *review* and left **unchanged**,
        so refusing here is the difference between a flagged value and a real
        customer name committed to a public repository. Passing
        ``accept_review=True`` records that the operator read those lines and
        judged them safe.
        """
        if not confirm:
            raise PermissionError(
                "refusing to write a fixture without confirm=True — review "
                "session.propose_fixture().diff_lines() first"
            )
        if self.sanitized is None:
            raise RuntimeError("call propose_fixture() before approving")
        report = self.sanitize_report
        if report is not None and report.needs_review and not accept_review:
            flagged = "\n  ".join(d.render() for d in report.review[:20])
            raise PermissionError(
                f"refusing to write: {len(report.review)} value(s) were left unchanged "
                f"because the sanitizer could not classify them from context:\n  {flagged}\n"
                "Confirm they identify no one, then re-approve with accept_review=True."
            )
        path = FIXTURES_DIR / f"{self.response_model_name}.json"
        path.write_text(
            json.dumps(self.sanitized, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        self.fixture_saved = True
        return path

    # -- mutation evidence ------------------------------------------------

    def record_restoration(
        self,
        *,
        record_identifier: str,
        precondition: str,
        mutation: str,
        expected_result: str,
        observed_result: str,
        restoration: str,
        final_state_verified: bool,
        evidence_ref: str | None = None,
        timestamp: str | None = None,
    ) -> MutationEvidence:
        """Capture the mutation evidence block (mutation handling)."""
        self.evidence = MutationEvidence(
            record_identifier=record_identifier,
            environment=self.environment,
            precondition=precondition,
            mutation=mutation,
            expected_result=expected_result,
            observed_result=observed_result,
            restoration=restoration,
            final_state_verified=final_state_verified,
            timestamp=timestamp
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            evidence_ref=evidence_ref,
        )
        needs = self.mutation_class and self.mutation_class.needs_restoration_evidence
        if needs:
            self.checks.add(
                "restoration",
                self.evidence.is_complete,
                "complete"
                if self.evidence.is_complete
                else f"missing: {self.evidence.missing_fields() or ['final_state_verified']}",
            )
        return self.evidence

    # -- evidence persistence ---------------------------------------------

    def write_evidence(self, *, status: str = "passing") -> dict:
        """Write/refresh schema-2 evidence (step 14). No manual JSON editing."""
        if self.mutation_class is None:
            raise MutationNotClassified("classify the endpoint before writing evidence")

        needs = self.mutation_class.needs_restoration_evidence
        if needs and not (self.evidence and self.evidence.is_complete):
            raise ValueError(
                f"{self.endpoint_key} is {self.mutation_class.value} and requires "
                "complete restoration evidence — call record_restoration(...) first"
            )

        entry: dict[str, Any] = {
            "status": status,
            "checked": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": "workbench",
            "environment": self.environment,
            "mutation_class": self.mutation_class.value,
            # A 204 endpoint has no response body, so no fixture to name.
            "fixture": f"{self.response_model_name}.json" if self.response_model_name else None,
            # MUST come from the same function the verifier uses
            # (ab.progress.certification.fixture_sha256, which hashes the file
            # bytes on disk). Hashing the in-memory payload instead produces a
            # different digest for identical content, and every endpoint would
            # be reported stale the moment it was certified.
            "fixture_sha256": (
                committed_fixture_sha256(self.response_model_name)
                if self.response_model_name else None
            ),
            "detail": None,
        }
        if self.sanitize_report:
            # Provenance, not diff size: "this payload went through the sanitizer".
            # A clean capture legitimately needs zero rewrites, and recording that
            # as sanitized=False would read as "this was never sanitized".
            entry["sanitized"] = True
            entry["sanitizer_changes"] = self.sanitize_report.changed_count
            entry["sanitizer_review"] = len(self.sanitize_report.review)
            entry["live_sha256"] = self.sanitize_report.live_sha256
        if self.evidence:
            ev = {
                k: v
                for k, v in self.evidence.__dict__.items()
                if not k.startswith("_")
            }
            entry["evidence"] = ev

        data = {"schema": 2, "results": {}}
        if RUN_RESULTS.is_file():
            existing = json.loads(RUN_RESULTS.read_text(encoding="utf-8"))
            data["results"] = existing.get("results", {})
            if "_comment" in existing:
                data["_comment"] = existing["_comment"]
        data["results"][self.endpoint_key] = entry
        data["results"] = dict(sorted(data["results"].items()))
        ordered = {"schema": 2}
        if "_comment" in data:
            ordered["_comment"] = data["_comment"]
        ordered["results"] = data["results"]
        RUN_RESULTS.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
        return entry

    def regenerate_report(self) -> int:
        """Regenerate ``html/progress.html`` (step 15)."""
        import subprocess
        import sys

        return subprocess.call(
            [sys.executable, "scripts/generate_progress.py"], cwd=str(REPO_ROOT)
        )

    # -- status ------------------------------------------------------------

    def certification_state(self):
        """Live certification record for this endpoint, post-evidence."""
        from ab.progress.certification import build_certification

        return next(
            (r for r in build_certification() if r.endpoint_key == self.endpoint_key),
            None,
        )
