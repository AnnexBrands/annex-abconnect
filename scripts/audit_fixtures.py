#!/usr/bin/env python
"""Audit (and optionally sanitize) every committed fixture. See issue #70.

    python scripts/audit_fixtures.py             # report only, writes FIXTURE_AUDIT.md
    python scripts/audit_fixtures.py --apply     # rewrite high-confidence values
    python scripts/audit_fixtures.py --check     # exit 1 if anything unsanitized remains

``--apply`` never touches an ambiguous value; those are listed in the report for
an operator to decide. Sanitization is deterministic and idempotent, so running
it twice changes nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ab.progress.fixture_audit import (  # noqa: E402
    audit_repository,
    render_markdown,
    sanitize_repository,
)

REPORT = REPO_ROOT / "FIXTURE_AUDIT.md"


def main() -> int:
    apply = "--apply" in sys.argv
    check = "--check" in sys.argv

    if apply:
        changed = sanitize_repository(dry_run=False)
        total = sum(n for _, n, _, _ in changed)
        print(f"sanitized {total} value(s) across {len(changed)} file(s)")
        for rel, n, before, after in changed:
            print(f"  {rel:52} {n:>4} values  {before[:8]} -> {after[:8]}")

    result = audit_repository()
    summary = result.summary()

    if check:
        if result.unsafe:
            print(
                f"FAIL: {summary['unsafe_files']} fixture(s) contain "
                f"{summary['high_detections']} unsanitized sensitive value(s).\n"
                "Run: python scripts/audit_fixtures.py --apply"
            )
            for f in result.unsafe[:10]:
                print(f"  {f.path}: {f.kinds()}")
            return 1
        print(f"OK: {summary['files']} fixtures clean of high-confidence sensitive data")
        return 0

    REPORT.write_text(render_markdown(result), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    for k, v in summary.items():
        print(f"  {k:22} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
