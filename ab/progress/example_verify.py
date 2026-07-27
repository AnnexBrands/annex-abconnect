"""Compare an example's produced output to its committed fixture (feature 037).

Thin adapter over :mod:`ab.progress.compare`, which is the single home for the
comparison policy and is shared with the certification workbench so the harness
and the notebook cannot reach different verdicts about the same endpoint.

The policy itself moved there when value equality was found to be unusable:
committed fixtures are sanitized, so their values differ from live by design and
every sanitized endpoint reported a false failure. See that module for the
reasoning; this file only adapts the result to the ``(matches, detail)`` shape
``scripts/run_examples.py`` consumes.
"""

from __future__ import annotations

from typing import Any

from ab.progress.compare import (
    VOLATILE_KEYS,
    ComparisonReport,
    is_volatile_key,
)
from ab.progress.compare import compare as compare_structure

__all__ = [
    "VOLATILE_KEYS",
    "ComparisonReport",
    "compare",
    "compare_structure",
    "is_volatile_key",
    "normalize",
]


def normalize(obj: Any) -> Any:
    """Recursively drop volatile keys so stable structure can be compared."""
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items() if not is_volatile_key(str(k))}
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    return obj


def compare(produced: Any, expected: Any, *, model: Any = None) -> tuple[bool, str | None]:
    """Return ``(matches, detail)`` for produced vs expected (fixture) JSON.

    *detail* is ``None`` on a match, else a compact structural explanation.
    """
    report = compare_structure(produced, expected, model=model)
    return report.ok, report.detail()
