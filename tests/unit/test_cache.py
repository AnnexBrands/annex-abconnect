"""Unit tests for cache-backed code resolution."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

from ab.cache import CodeResolver


def test_resolve_accepts_uuid_objects_without_lookup():
    resolver = CodeResolver(MagicMock(name="client"), "secret")
    company_id = UUID("850be91a-c706-e811-8f3f-00155d426802")

    assert resolver.resolve(company_id) == "850be91a-c706-e811-8f3f-00155d426802"
