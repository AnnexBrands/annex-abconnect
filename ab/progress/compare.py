"""Shared structural comparison for the harness and the workbench.

A committed fixture is **sanitized**: its values deliberately differ from the
live response that produced it. Comparing the two by value therefore reports a
failure for every endpoint whose fixture contains substituted data -- which is
every endpoint carrying a name, an email, a coordinate or an id. That is how
``api.address.validate`` came to be reported as failing while it was in fact
certified: the fixture held ``34.05 / -74.01`` from the sanitizer's synthetic
coordinate pool and live staging returned the real San Diego pair.

So certification compares *shape*, not values:

- the response parses into its declared pydantic model,
- it carries no undeclared fields,
- keys and nested structure match the fixture,
- JSON value types match (this is what catches ``"2."`` arriving where an
  ``int`` is declared, and an ``int`` id arriving where a ``str`` is declared),
- list element shapes match, merged across elements so element count and
  ordering -- which vary run to run -- are not drift.

Values are never compared, so sanitized substitutions and volatile fields
cannot produce a false failure. Nullability is recorded but tolerated: whether
an optional field happens to be populated on the test account is data variance,
not a contract change, and the model-parse check already constrains it.

This is deliberately not "do the top-level keys match". A response that kept
its outer keys but changed a nested list element's types would pass such a test
and fail in production.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

#: Keys dropped anywhere in the tree before comparison (lower-cased, underscore-free).
VOLATILE_KEYS: set[str] = {
    "correlationid",
    "requestid",
    "traceid",
    "servertime",
    "timestamp",
}

# Date/time fields are matched on a real boundary -- a camelCase suffix (capital
# D/T) or a snake ``_suffix`` -- NOT a bare substring. This avoids silently
# dropping meaningful fields that merely end in those letters:
# ``allowJobInfoUpdate``, ``dontValidate``, ``runtime``, ``lifetime``,
# ``candidate`` (the UAT-era bug where a genuine mismatch was reported a match).
_VOLATILE_CAMEL_RE = re.compile(r"(?:Date|DateTime|Timestamp|Ticks|Time|Utc)$")
_VOLATILE_SNAKE_RE = re.compile(r"(?:^|_)(?:date|datetime|timestamp|ticks|time|utc)$")

_MAX_DETAIL_LINES = 40

#: Shape token for a list that had no elements to learn a shape from.
EMPTY = "empty"
#: Shape token for a JSON null.
NULL = "null"


def is_volatile_key(key: str) -> bool:
    """True when *key* names a per-request or clock-derived value."""
    if key.replace("_", "").lower() in VOLATILE_KEYS:
        return True
    return bool(_VOLATILE_CAMEL_RE.search(key) or _VOLATILE_SNAKE_RE.search(key))


def json_kind(value: Any) -> str:
    """The JSON type name of a scalar.

    ``int`` and ``float`` collapse to ``number``: JSON does not distinguish them
    and ``0`` vs ``0.0`` is not drift. ``bool`` is kept separate from ``number``
    even though Python makes it an ``int`` subclass -- a flag turning into a
    count is a real contract change.
    """
    if value is None:
        return NULL
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def _merge(a: Any, b: Any) -> Any:
    """Merge two shapes into one that accepts both.

    Used across list elements: one element may populate a field another leaves
    null, and neither is authoritative on its own.
    """
    if a is None:
        return b
    if b is None:
        return a
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _merge(a.get(k), v)
        return out
    if isinstance(a, dict) or isinstance(b, dict):
        # An object on one side and a scalar on the other: keep both so the
        # diff reports the conflict rather than silently picking one.
        return {"__conflict__": f"{_describe(a)}|{_describe(b)}"}
    tokens = {t for t in str(a).split("|")} | {t for t in str(b).split("|")}
    tokens.discard(EMPTY)
    if not tokens:
        return EMPTY
    return "|".join(sorted(tokens))


def shape(node: Any) -> Any:
    """Reduce *node* to its structure: dicts of keys, merged list shapes, kinds."""
    if isinstance(node, dict):
        return {
            k: shape(v)
            for k, v in node.items()
            if not is_volatile_key(str(k))
        }
    if isinstance(node, list):
        merged: Any = None
        for item in node:
            merged = _merge(merged, shape(item))
        return EMPTY if merged is None else ["list", merged]
    return json_kind(node)


def _describe(node: Any) -> str:
    if isinstance(node, dict):
        return "object"
    if isinstance(node, list):
        return "list"
    return str(node)


@dataclass
class Diff:
    """One structural difference between a live response and its fixture."""

    path: str
    kind: str  # "missing" | "extra" | "type"
    detail: str

    def render(self) -> str:
        sign = {"missing": "-", "extra": "+", "type": "~"}.get(self.kind, "?")
        where = self.path or "<root>"
        return f"{sign} {where}: {self.detail}"


@dataclass
class ComparisonReport:
    """Structural verdict for one response against one fixture."""

    diffs: list[Diff] = field(default_factory=list)
    #: Paths where one side was null and the other populated (tolerated).
    nullable: list[str] = field(default_factory=list)
    #: Undeclared fields pydantic captured on the response model.
    extras: list[str] = field(default_factory=list)
    #: True/False when a model was supplied, None when it was not checked.
    parsed: bool | None = None
    parse_error: str | None = None
    #: False when there was no committed fixture to compare against.
    compared: bool = True

    @property
    def ok(self) -> bool:
        if self.parsed is False:
            return False
        return not self.diffs and not self.extras

    def detail(self, limit: int = _MAX_DETAIL_LINES) -> str | None:
        """A compact, reviewable explanation, or ``None`` when everything matched."""
        if self.ok:
            return None
        lines: list[str] = []
        if self.parsed is False:
            lines.append(f"! response does not parse into its declared model: {self.parse_error}")
        for e in self.extras[:limit]:
            lines.append(f"+ {e}: undeclared field on the response model")
        for d in self.diffs[:limit]:
            lines.append(d.render())
        overflow = len(self.diffs) + len(self.extras) - limit
        if overflow > 0:
            lines.append(f"... ({overflow} more)")
        return "\n".join(lines)

    def render(self) -> str:
        return self.detail() or "structure matches"


def _walk(expected: Any, produced: Any, path: str, out: ComparisonReport) -> None:
    if isinstance(expected, dict) and isinstance(produced, dict):
        for k in sorted(set(expected) - set(produced)):
            out.diffs.append(Diff(_join(path, k), "missing", "in fixture, absent live"))
        for k in sorted(set(produced) - set(expected)):
            out.diffs.append(Diff(_join(path, k), "extra", "live only, fixture stale"))
        for k in sorted(set(expected) & set(produced)):
            _walk(expected[k], produced[k], _join(path, k), out)
        return

    e_list = isinstance(expected, list) and expected and expected[0] == "list"
    p_list = isinstance(produced, list) and produced and produced[0] == "list"
    if e_list and p_list:
        _walk(expected[1], produced[1], f"{path}[]", out)
        return

    # A side that is EMPTY or NULL teaches nothing about the other side's shape:
    # an empty list or an unpopulated optional on the test account is data
    # variance, not drift. Record it and move on.
    if _is_unknown(expected) or _is_unknown(produced):
        if expected != produced:
            out.nullable.append(path or "<root>")
        return

    if isinstance(expected, dict) != isinstance(produced, dict) or e_list != p_list:
        out.diffs.append(
            Diff(path, "type", f"fixture {_describe(expected)}, live {_describe(produced)}")
        )
        return

    e_kinds = {t for t in str(expected).split("|")} - {NULL, EMPTY}
    p_kinds = {t for t in str(produced).split("|")} - {NULL, EMPTY}
    if not e_kinds or not p_kinds:
        if e_kinds != p_kinds:
            out.nullable.append(path or "<root>")
        return
    if not (e_kinds & p_kinds):
        out.diffs.append(
            Diff(
                path,
                "type",
                f"fixture {'|'.join(sorted(e_kinds))}, live {'|'.join(sorted(p_kinds))}",
            )
        )


def _is_unknown(node: Any) -> bool:
    if isinstance(node, (dict, list)):
        return False
    tokens = set(str(node).split("|"))
    return not (tokens - {NULL, EMPTY})


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def compare(
    produced: Any,
    expected: Any,
    *,
    model: Any = None,
) -> ComparisonReport:
    """Compare a live response to its committed fixture structurally.

    *produced* and *expected* are JSON-able payloads. *model* is the validated
    pydantic response instance, when the caller has one; supplying it enables
    the parse and undeclared-field checks.
    """
    report = ComparisonReport()

    if model is not None:
        from ab.progress.certify.summarize import extra_fields, is_model

        if is_model(model):
            report.parsed = True
            report.extras = sorted(extra_fields(model))
        else:
            report.parsed = None

    if expected is None:
        report.compared = False
        return report

    _walk(shape(expected), shape(produced), "", report)
    return report
