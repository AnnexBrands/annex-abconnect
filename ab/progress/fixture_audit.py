"""Repository-wide fixture safety audit (#70).

Committed fixtures are **sanitized structural evidence**, not raw API captures.
This module inventories every fixture, reports what sanitization would change,
and separates values it can rewrite confidently from values that need an
operator decision.

Two entry points:

* :func:`audit_repository` -- read-only inventory, backs both the audit report
  and the repository-wide safety test.
* :func:`sanitize_repository` -- applies :func:`ab.progress.sanitize.sanitize`
  to every fixture, rewriting only high-confidence detections.

Nothing here rewrites a questionable value silently: everything ambiguous
surfaces in :attr:`FixtureFinding.review` for a human to decide.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ab.progress.sanitize import Detection, audit, payload_sha256, sanitize

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@dataclass
class FixtureFinding:
    """Audit result for one fixture file."""

    path: str
    detections: list[Detection] = field(default_factory=list)
    sha256: str | None = None
    error: str | None = None

    @property
    def high(self) -> list[Detection]:
        return [d for d in self.detections if d.rewritten]

    @property
    def review(self) -> list[Detection]:
        return [d for d in self.detections if not d.rewritten]

    @property
    def is_safe(self) -> bool:
        """No high-confidence sensitive value remains in this fixture."""
        return not self.high and not self.error

    def kinds(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.high:
            out[d.kind.value] = out.get(d.kind.value, 0) + 1
        return out


@dataclass
class AuditResult:
    """The whole-repository picture."""

    findings: list[FixtureFinding] = field(default_factory=list)

    @property
    def unsafe(self) -> list[FixtureFinding]:
        return [f for f in self.findings if f.high]

    @property
    def needs_review(self) -> list[FixtureFinding]:
        return [f for f in self.findings if f.review]

    @property
    def errored(self) -> list[FixtureFinding]:
        return [f for f in self.findings if f.error]

    def summary(self) -> dict[str, int]:
        return {
            "files": len(self.findings),
            "unsafe_files": len(self.unsafe),
            "high_detections": sum(len(f.high) for f in self.findings),
            "review_detections": sum(len(f.review) for f in self.findings),
            "unreadable": len(self.errored),
        }

    def kind_totals(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.findings:
            for k, n in f.kinds().items():
                out[k] = out.get(k, 0) + n
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def iter_fixture_files(root: Path | None = None) -> list[Path]:
    """Every committed fixture JSON, live and mock, sorted for stable output."""
    base = root or FIXTURES_DIR
    if not base.is_dir():
        return []
    return sorted(base.rglob("*.json"))


def audit_repository(root: Path | None = None) -> AuditResult:
    """Detect (never rewrite) sensitive values across every fixture."""
    result = AuditResult()
    for path in iter_fixture_files(root):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            result.findings.append(FixtureFinding(rel, error=str(exc)))
            continue
        report = audit(data)
        result.findings.append(
            FixtureFinding(rel, list(report.detections), payload_sha256(data))
        )
    return result


def sanitize_repository(
    root: Path | None = None, *, dry_run: bool = True
) -> list[tuple[str, int, str, str]]:
    """Sanitize every fixture in place.

    Returns ``(relative_path, values_changed, before_sha, after_sha)`` for each
    file that would change. With ``dry_run`` (the default) nothing is written --
    the caller decides, which is the same consent rule the workbench applies.
    """
    changed: list[tuple[str, int, str, str]] = []
    for path in iter_fixture_files(root):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cleaned, report = sanitize(data)
        if not report.changes:
            continue
        before, after = payload_sha256(data), payload_sha256(cleaned)
        changed.append((rel, len(report.changes), before, after))
        if not dry_run:
            path.write_text(
                json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    return changed


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------


def render_markdown(result: AuditResult, *, sample: int = 3) -> str:
    """Human-readable audit report (written to ``FIXTURE_AUDIT.md``)."""
    s = result.summary()
    lines = [
        "# Fixture Safety Audit",
        "",
        "Generated by `python scripts/audit_fixtures.py`. Committed fixtures are",
        "**sanitized structural evidence**, not raw API captures.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Fixture files scanned | {s['files']} |",
        f"| Files with unsanitized sensitive values | **{s['unsafe_files']}** |",
        f"| High-confidence detections (auto-sanitized) | {s['high_detections']} |",
        f"| Ambiguous detections (operator review) | {s['review_detections']} |",
        f"| Unreadable files | {s['unreadable']} |",
        "",
    ]

    if result.kind_totals():
        lines += ["## High-confidence detections by kind", "", "| Kind | Count |", "|---|---|"]
        lines += [f"| {k} | {n} |" for k, n in result.kind_totals().items()]
        lines.append("")

    if result.unsafe:
        lines += [
            "## Files still carrying unsanitized values",
            "",
            "These are rewritten by `python scripts/audit_fixtures.py --apply`.",
            "",
        ]
        for f in sorted(result.unsafe, key=lambda x: -len(x.high)):
            kinds = ", ".join(f"{k}×{n}" for k, n in f.kinds().items())
            lines.append(f"### `{f.path}` — {len(f.high)} value(s): {kinds}")
            lines += [f"- `{d.path}` [{d.kind.value}]" for d in f.high[:sample]]
            if len(f.high) > sample:
                lines.append(f"- …and {len(f.high) - sample} more")
            lines.append("")
    else:
        lines += ["## Files still carrying unsanitized values", "", "None. ✅", ""]

    if result.needs_review:
        total = sum(len(f.review) for f in result.needs_review)
        lines += [
            "## Needs operator review",
            "",
            f"{total} value(s) across {len(result.needs_review)} file(s) are plausibly",
            "sensitive but ambiguous — a bare `name` that may be an enum label, or a",
            "generic identifier. **These were not rewritten.** Silently changing them",
            "would corrupt reference data and make the diff untrustworthy.",
            "",
            "| File | Values | Sample paths |",
            "|---|---|---|",
        ]
        for f in sorted(result.needs_review, key=lambda x: -len(x.review))[:25]:
            paths = ", ".join(f"`{d.path}`" for d in f.review[:2])
            lines.append(f"| `{f.path}` | {len(f.review)} | {paths} |")
        if len(result.needs_review) > 25:
            lines.append(f"| …{len(result.needs_review) - 25} more files | | |")
        lines.append("")

    if result.errored:
        lines += ["## Unreadable", ""]
        lines += [f"- `{f.path}`: {f.error}" for f in result.errored]
        lines.append("")

    return "\n".join(lines)
