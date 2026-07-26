"""Endpoint inventory reconciliation (issue #69).

The progress artifact previously carried three different denominators for one
question -- 209 (a stale gate docstring), 218, and 235 -- with nothing
explaining the relationship. This module makes the two real inventories
explicit and pins how they relate.

Two distinct populations:

* **Public endpoints** (218) -- public, discoverable SDK methods that carry a
  :class:`~ab.api.route.Route`. This is the **certification denominator**: it
  is what a caller can actually invoke, so it is what "is this endpoint
  certified?" must be measured against.
* **Module-level Route objects** (235) -- every ``Route`` instance bound to a
  module attribute anywhere under ``ab.api.endpoints``. This is what the
  fixture/gate feeds walk, because gates are keyed by ``(path, METHOD)``.

The 17-route gap is not drift. It decomposes exactly:

.. code-block:: text

    235 module-level Route objects
     = 217 bound directly to a public discoverable method
     + 18  internal shared Route constants

The 18 are underscore-prefixed module constants (``_BOL``, ``_INVOICE``,
``_LIST``, ``_GET_AGENT``, ...). Every one is referenced internally -- ``_BOL``
alone backs five public methods (``bol``/``hbl``/``pbl``/``dbl``/...) via
``self._pdf(_BOL, ...)``. They are a deliberate one-Route-to-many-methods
pattern, **not** dead or duplicated code.

217 Route objects back 218 public methods because
``api.jobs.freight_providers.final_override`` and
``api.jobs.freight_providers.save`` share a single ``Route`` instance.
"""

from __future__ import annotations

import ast
import pathlib
from dataclasses import dataclass
from enum import Enum


class RouteClass(str, Enum):
    """How a module-level ``Route`` object relates to the public SDK surface."""

    #: Bound directly to at least one public, discoverable SDK method.
    PUBLIC = "public"
    #: An underscore-prefixed module constant referenced by public method bodies.
    INTERNAL_SHARED = "internal_shared"
    #: Collides with another Route on ``(normalized_path, METHOD)``.
    DUPLICATE = "duplicate"
    #: Reachable from no public method and referenced by no code -- dead.
    ORPHANED = "orphaned"


@dataclass(frozen=True)
class RouteRecord:
    """One module-level ``Route`` object and how it is reached."""

    module: str
    attr: str
    http_method: str
    path: str
    classification: RouteClass
    internal_uses: int
    public_keys: tuple[str, ...]


@dataclass(frozen=True)
class Reconciliation:
    """The full inventory picture, as reported by :func:`reconcile`."""

    public_endpoint_keys: tuple[str, ...]
    route_records: tuple[RouteRecord, ...]

    @property
    def public_count(self) -> int:
        """Certification denominator: public discoverable methods with a Route."""
        return len(self.public_endpoint_keys)

    @property
    def route_object_count(self) -> int:
        """Every module-level ``Route`` object (the gate/fixture feed population)."""
        return len(self.route_records)

    def by_class(self, kind: RouteClass) -> tuple[RouteRecord, ...]:
        return tuple(r for r in self.route_records if r.classification is kind)

    @property
    def unattached(self) -> tuple[RouteRecord, ...]:
        """Routes not bound to any public method (internal, duplicate, or orphaned)."""
        return tuple(
            r for r in self.route_records if r.classification is not RouteClass.PUBLIC
        )

    def summary(self) -> dict[str, int]:
        return {
            "public_endpoints": self.public_count,
            "route_objects": self.route_object_count,
            "routes_bound_to_public": len(self.by_class(RouteClass.PUBLIC)),
            "internal_shared": len(self.by_class(RouteClass.INTERNAL_SHARED)),
            "duplicate": len(self.by_class(RouteClass.DUPLICATE)),
            "orphaned": len(self.by_class(RouteClass.ORPHANED)),
        }


def public_endpoint_keys() -> tuple[str, ...]:
    """Every public discoverable endpoint as ``api.<group>.<method>``, sorted.

    The certification denominator. Sourced from the live registry, so it cannot
    drift from the code the way a hand-maintained list would.
    """
    from ab.cli.discovery import discover_endpoints_from_class

    keys: set[str] = set()
    for name, info in discover_endpoints_from_class().items():
        for m in info.methods:
            if m.route is not None:
                keys.add(f"api.{name}.{m.name}")
    return tuple(sorted(keys))


def _load_count(module_file: str, attr: str) -> int:
    """Count ``Load`` references to *attr* in *module_file* (its own assignment aside)."""
    try:
        tree = ast.parse(pathlib.Path(module_file).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return 0
    return sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and n.id == attr and isinstance(n.ctx, ast.Load)
    )


def reconcile() -> Reconciliation:
    """Classify every module-level ``Route`` against the public SDK surface."""
    import ab.api.endpoints as endpoints_pkg
    from ab.api.route import Route
    from ab.cli.discovery import discover_endpoints_from_class
    from ab.progress.route_index import _iter_endpoint_modules, normalize_path

    # Route object id -> the public method keys it backs.
    public_by_id: dict[int, list[str]] = {}
    for name, info in discover_endpoints_from_class().items():
        for m in info.methods:
            if m.route is not None:
                public_by_id.setdefault(id(m.route), []).append(f"api.{name}.{m.name}")

    seen: set[int] = set()
    records: list[RouteRecord] = []
    key_counts: dict[tuple[str, str], int] = {}

    for module in _iter_endpoint_modules(endpoints_pkg):
        for attr in dir(module):
            obj = getattr(module, attr)
            if not isinstance(obj, Route) or id(obj) in seen:
                continue
            seen.add(id(obj))
            key = (normalize_path(obj.path), obj.method)
            key_counts[key] = key_counts.get(key, 0) + 1
            public_keys = tuple(sorted(public_by_id.get(id(obj), ())))
            uses = _load_count(module.__file__, attr) if not public_keys else 0

            if public_keys:
                klass = RouteClass.PUBLIC
            elif uses:
                klass = RouteClass.INTERNAL_SHARED
            else:
                klass = RouteClass.ORPHANED

            records.append(
                RouteRecord(
                    module=module.__name__,
                    attr=attr,
                    http_method=obj.method,
                    path=obj.path,
                    classification=klass,
                    internal_uses=uses,
                    public_keys=public_keys,
                )
            )

    # Promote genuine (path, METHOD) collisions to DUPLICATE.
    dup_keys = {k for k, n in key_counts.items() if n > 1}
    if dup_keys:
        records = [
            (
                r
                if (normalize_path(r.path), r.http_method) not in dup_keys
                else RouteRecord(
                    module=r.module,
                    attr=r.attr,
                    http_method=r.http_method,
                    path=r.path,
                    classification=RouteClass.DUPLICATE,
                    internal_uses=r.internal_uses,
                    public_keys=r.public_keys,
                )
            )
            for r in records
        ]

    records.sort(key=lambda r: (r.module, r.attr))
    return Reconciliation(
        public_endpoint_keys=public_endpoint_keys(),
        route_records=tuple(records),
    )
