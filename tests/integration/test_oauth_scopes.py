"""The per-environment scope defaults must be accepted by the real servers.

The whole grant fails with ``invalid_scope`` if one requested scope is not
provisioned, so a default that drifts from what a server offers breaks *all*
authentication for that environment. That is exactly how the ``catalog`` scope
-- staging-only -- would have broken production, so it is pinned here against
both IdentityServers rather than against a fixture.
"""

from __future__ import annotations

import requests

from ab.config import load_settings

pytestmark = __import__("pytest").mark.live

DISCOVERY = {
    "staging": "https://login.staging.abconnect.co/.well-known/openid-configuration",
    "production": "https://login.abconnect.co/.well-known/openid-configuration",
}


def _supported_scopes(environment: str) -> set[str]:
    resp = requests.get(DISCOVERY[environment], timeout=30)
    resp.raise_for_status()
    return set(resp.json().get("scopes_supported", []))


def test_staging_default_scopes_are_all_advertised():
    settings = load_settings(env="staging", require_credentials=False)
    requested = set(settings.oauth_scopes.split())
    assert requested <= _supported_scopes("staging"), (
        "staging default requests a scope the server does not advertise; "
        "the grant would fail with invalid_scope"
    )


def test_production_default_scopes_are_all_advertised():
    settings = load_settings(env="production", require_credentials=False)
    requested = set(settings.oauth_scopes.split())
    assert requested <= _supported_scopes("production"), (
        "production default requests a scope the server does not advertise; "
        "the grant would fail with invalid_scope"
    )


def test_catalog_scope_is_staging_only():
    """When this fails, production has gained the catalog scope: move it into
    the production tuple in ``ABConnectSettings._DEFAULT_SCOPES``."""
    assert "catalog" in _supported_scopes("staging")
    assert "catalog" not in _supported_scopes("production"), (
        "production now offers the catalog scope — add it to the production "
        "default in ab/config.py::ABConnectSettings._DEFAULT_SCOPES"
    )


def test_staging_grant_succeeds_with_the_default_scopes():
    """End to end: the default set actually mints a token."""
    settings = load_settings(env="staging")
    resp = requests.post(
        settings.identity_url,
        data={
            "grant_type": "password",
            "username": settings.username,
            "password": settings.password,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "scope": settings.oauth_scopes,
        },
        timeout=30,
    )
    assert resp.ok, f"staging default scopes rejected: {resp.status_code} {resp.text}"
    granted = set(resp.json()["scope"].split())
    assert granted == set(settings.oauth_scopes.split())
    assert "catalog" in granted
