"""Pin the two endpoint inventories and their relationship (issue #69).

The progress artifact previously carried three denominators for one question --
209 (a stale gate docstring), 218, and 235 -- with nothing explaining how they
related. These tests pin both populations and the arithmetic between them, so a
future change either keeps the relationship or fails loudly here.
"""

from __future__ import annotations

from ab.progress.inventory import RouteClass, reconcile

#: Public discoverable SDK methods carrying a Route. The certification denominator.
EXPECTED_PUBLIC_ENDPOINTS = 218

#: Every module-level Route object under ab.api.endpoints (the gate/fixture feed).
EXPECTED_ROUTE_OBJECTS = 235

#: Underscore-prefixed module constants shared by several public methods.
EXPECTED_INTERNAL_SHARED = 18


def test_public_endpoint_inventory_is_pinned() -> None:
    r = reconcile()
    assert r.public_count == EXPECTED_PUBLIC_ENDPOINTS, (
        f"public endpoint count moved to {r.public_count}; if intentional, update "
        "EXPECTED_PUBLIC_ENDPOINTS and the certification denominator together"
    )


def test_route_object_inventory_is_pinned() -> None:
    r = reconcile()
    assert r.route_object_count == EXPECTED_ROUTE_OBJECTS


def test_inventories_reconcile_exactly() -> None:
    """235 route objects = 217 bound to public methods + 18 internal constants."""
    r = reconcile()
    bound = len(r.by_class(RouteClass.PUBLIC))
    internal = len(r.by_class(RouteClass.INTERNAL_SHARED))
    assert bound + internal == r.route_object_count
    assert internal == EXPECTED_INTERNAL_SHARED


def test_no_orphaned_or_duplicate_routes() -> None:
    """Every Route is reachable: bound to a public method or used internally."""
    r = reconcile()
    orphaned = r.by_class(RouteClass.ORPHANED)
    duplicate = r.by_class(RouteClass.DUPLICATE)
    assert not orphaned, "dead Route objects:\n  " + "\n  ".join(
        f"{x.module}.{x.attr} {x.http_method} {x.path}" for x in orphaned
    )
    assert not duplicate, "colliding Route objects:\n  " + "\n  ".join(
        f"{x.module}.{x.attr} {x.http_method} {x.path}" for x in duplicate
    )


def test_internal_routes_are_all_actually_referenced() -> None:
    """The 18 internal constants must each be used, or they are dead code."""
    r = reconcile()
    for rec in r.by_class(RouteClass.INTERNAL_SHARED):
        assert rec.internal_uses > 0, f"{rec.module}.{rec.attr} is never referenced"
        assert rec.attr.startswith("_"), (
            f"{rec.module}.{rec.attr} is unattached but not underscore-prefixed — "
            "either bind it to a public method or mark it private"
        )


def test_public_count_exceeds_bound_routes_by_the_shared_route() -> None:
    """218 public methods are backed by 217 Route objects.

    ``api.jobs.freight_providers.final_override`` and ``.save`` share one Route
    instance. Pinning this stops the two counts silently drifting apart.
    """
    r = reconcile()
    bound = len(r.by_class(RouteClass.PUBLIC))
    assert r.public_count - bound == 1

    shared = [rec for rec in r.by_class(RouteClass.PUBLIC) if len(rec.public_keys) > 1]
    assert len(shared) == 1
    assert set(shared[0].public_keys) == {
        "api.jobs.freight_providers.final_override",
        "api.jobs.freight_providers.save",
    }


def test_certification_denominator_matches_example_index() -> None:
    """The certification denominator and the coverage gate must agree."""
    from ab.progress.example_index import routed_endpoint_keys

    r = reconcile()
    assert set(r.public_endpoint_keys) == routed_endpoint_keys()
