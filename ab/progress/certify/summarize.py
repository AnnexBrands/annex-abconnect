"""Compact representations for large responses (issue #71).

Several endpoints return payloads that are thousands of lines as raw ``repr``.
Printing those into a notebook buries the one fact the operator needs -- did
this look right? -- under pages of scroll. Everything here is bounded by
default and expandable on request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Field names that identify a record, in the order we prefer to show them.
_ID_HINTS = (
    "id", "uuid", "guid", "code", "number", "displayid", "jobdisplayid",
    "jobid", "key", "reference", "name", "title", "status",
)


def _is_identifier(key: str) -> bool:
    k = key.lower().replace("_", "")
    return any(k == h or k.endswith(h) for h in _ID_HINTS)


def _count_populated(node: Any) -> tuple[int, int]:
    """Return ``(populated, total)`` scalar leaves under *node*."""
    if isinstance(node, dict):
        pop = tot = 0
        for v in node.values():
            p, t = _count_populated(v)
            pop += p
            tot += t
        return pop, tot
    if isinstance(node, list):
        pop = tot = 0
        for v in node:
            p, t = _count_populated(v)
            pop += p
            tot += t
        return pop, tot
    return (0 if node is None or node == "" else 1), 1


def _declared_fields(obj: Any) -> dict | None:
    """Model fields read from the *class* — instance access is deprecated in V2.11."""
    return getattr(type(obj), "model_fields", None)


def is_model(obj: Any) -> bool:
    """True when *obj* is a pydantic model instance."""
    return _declared_fields(obj) is not None


def extra_fields(model: Any) -> dict[str, Any]:
    """Undeclared fields pydantic captured on *model* (recursively)."""
    out: dict[str, Any] = {}

    def walk(obj: Any, path: str) -> None:
        extra = getattr(obj, "__pydantic_extra__", None)
        if extra:
            for k, v in extra.items():
                out[f"{path}.{k}" if path else k] = v
        fields = _declared_fields(obj)
        if not fields:
            return
        for name in fields:
            val = getattr(obj, name, None)
            if is_model(val):
                walk(val, f"{path}.{name}" if path else name)
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if is_model(item):
                        walk(item, f"{path}.{name}[{i}]" if path else f"{name}[{i}]")

    walk(model, "")
    return out


def select_path(payload: Any, path: str) -> Any:
    """Select a nested path like ``items[0].address.city`` from a payload."""
    cur = payload
    for part in path.replace("]", "").replace("[", ".").split("."):
        if not part:
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


@dataclass
class ResponseSummary:
    """Bounded view of a response -- what the notebook prints by default."""

    model_type: str
    identifiers: dict[str, Any] = field(default_factory=dict)
    populated: int = 0
    total: int = 0
    extras: dict[str, Any] = field(default_factory=dict)
    item_count: int | None = None
    json_bytes: int = 0
    payload: Any = None

    @property
    def populated_pct(self) -> float:
        return (self.populated / self.total * 100) if self.total else 0.0

    def render(self) -> str:
        """One compact block. Never dumps the payload."""
        lines = [f"model      : {self.model_type}"]
        if self.item_count is not None:
            lines.append(f"items      : {self.item_count}")
        if self.identifiers:
            shown = ", ".join(f"{k}={v!r}" for k, v in list(self.identifiers.items())[:6])
            lines.append(f"identifiers: {shown}")
        lines.append(
            f"populated  : {self.populated}/{self.total} fields "
            f"({self.populated_pct:.0f}%)"
        )
        lines.append(f"size       : {self.json_bytes:,} bytes of JSON")
        if self.extras:
            names = ", ".join(list(self.extras)[:8])
            lines.append(f"⚠ undeclared fields ({len(self.extras)}): {names}")
        else:
            lines.append("undeclared : none")
        return "\n".join(lines)

    def full_json(self, indent: int = 2, max_chars: int | None = 20000) -> str:
        """The complete payload, explicitly requested and still bounded."""
        import json

        text = json.dumps(self.payload, indent=indent, default=str)
        if max_chars is not None and len(text) > max_chars:
            return (
                text[:max_chars]
                + f"\n… truncated at {max_chars:,} chars "
                f"(total {len(text):,}); pass max_chars=None for everything"
            )
        return text

    def path(self, path: str) -> Any:
        """Drill into one nested path instead of printing the whole payload."""
        return select_path(self.payload, path)

    def _repr_pretty_(self, p, cycle):  # pragma: no cover - notebook display hook
        p.text(self.render())

    def __repr__(self) -> str:
        return self.render()


def summarize(model: Any, payload: Any | None = None) -> ResponseSummary:
    """Build a bounded summary of a validated response model."""
    import json

    if payload is None:
        if hasattr(model, "model_dump"):
            payload = model.model_dump(by_alias=True, mode="json")
        else:
            payload = model

    root = payload
    item_count = None
    if isinstance(payload, list):
        item_count = len(payload)
        root = payload[0] if payload else {}
    elif isinstance(payload, dict):
        for key in ("items", "results", "data", "value"):
            if isinstance(payload.get(key), list):
                item_count = len(payload[key])
                break

    identifiers: dict[str, Any] = {}
    if isinstance(root, dict):
        for k, v in root.items():
            if _is_identifier(k) and not isinstance(v, (dict, list)) and v is not None:
                identifiers[k] = v

    populated, total = _count_populated(payload)
    return ResponseSummary(
        model_type=type(model).__name__,
        identifiers=identifiers,
        populated=populated,
        total=total,
        extras=extra_fields(model) if is_model(model) else {},
        item_count=item_count,
        json_bytes=len(json.dumps(payload, default=str)),
        payload=payload,
    )
