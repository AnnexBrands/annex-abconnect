"""OAuth scopes are configurable and default per environment.

The staging IdentityServer offers a ``catalog`` scope; production does not, and
the server rejects the *entire* grant with ``invalid_scope`` when any single
requested scope is unavailable. So the default cannot be one shared list --
these tests pin the per-environment defaults and the override path.
"""

from __future__ import annotations

import pytest

from ab.config import ABConnectSettings
from ab.exceptions import AuthenticationError
from ab.http import HttpClient


def _settings(**kwargs) -> ABConnectSettings:
    base = dict(
        username="u", password="p", client_id="toolsApp", client_secret="s",
        require_credentials=False,
    )
    base.update(kwargs)
    return ABConnectSettings(**base)


class TestScopeDefaults:
    def test_staging_default_includes_catalog(self):
        assert _settings(environment="staging").oauth_scopes == (
            "roles portalApi customerPortalApi catalog offline_access"
        )

    def test_production_default_omits_catalog(self):
        """Production answers invalid_scope for ``catalog``; it must not be sent."""
        scopes = _settings(environment="production").oauth_scopes
        assert scopes == "roles portalApi customerPortalApi offline_access"
        assert "catalog" not in scopes

    @pytest.mark.parametrize("environment", ["staging", "production"])
    def test_every_default_keeps_offline_access(self, environment):
        """Without it the server issues no refresh token and every session
        falls back to a password grant."""
        assert "offline_access" in _settings(environment=environment).oauth_scopes.split()

    @pytest.mark.parametrize("environment", ["staging", "production"])
    def test_explicit_scopes_override_the_default(self, environment):
        assert _settings(environment=environment, scopes="catalog").oauth_scopes == "catalog"

    def test_empty_string_is_honoured_not_treated_as_unset(self):
        assert _settings(environment="staging", scopes="").oauth_scopes == ""

    def test_scopes_read_from_environment(self, monkeypatch):
        """Constructed directly rather than through ``load_settings``: that
        helper also requires client credentials, which a bare CI checkout has
        no ``.env`` to supply."""
        monkeypatch.setenv("ABCONNECT_SCOPES", "roles offline_access")
        settings = ABConnectSettings(
            client_id="toolsApp", client_secret="s",
            require_credentials=False, environment="staging",
        )
        assert settings.oauth_scopes == "roles offline_access"


class _Resp:
    def __init__(self, status_code=400, payload=None, text=""):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._payload = payload
        self.text = text or str(payload)

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class TestGrantUsesConfiguredScopes:
    def _client(self, monkeypatch, settings, resp):
        sent = {}

        def fake_post(url, data=None, timeout=None):
            sent.update(data or {})
            return resp

        monkeypatch.setattr("ab.http.requests.post", fake_post)
        client = HttpClient.__new__(HttpClient)
        client._settings = settings
        return client, sent

    def test_password_grant_sends_the_configured_scope(self, monkeypatch):
        settings = _settings(environment="staging")
        resp = _Resp(200, {"access_token": "t", "expires_in": 3600})
        client, sent = self._client(monkeypatch, settings, resp)
        client._store_token = lambda payload: payload

        client._password_grant_with(username="u", password="p")

        assert sent["scope"] == "roles portalApi customerPortalApi catalog offline_access"

    def test_invalid_scope_error_names_scopes_client_and_setting(self, monkeypatch):
        settings = _settings(environment="production")
        resp = _Resp(400, {"error": "invalid_scope"})
        client, _ = self._client(monkeypatch, settings, resp)

        with pytest.raises(AuthenticationError) as exc:
            client._password_grant_with(username="u", password="p")

        message = str(exc.value)
        assert "Requested scopes:" in message
        assert "toolsApp" in message
        assert "production" in message
        assert "ABCONNECT_SCOPES" in message

    def test_other_failures_keep_the_plain_message(self, monkeypatch):
        settings = _settings(environment="staging")
        resp = _Resp(401, {"error": "invalid_grant"}, text="bad creds")
        client, _ = self._client(monkeypatch, settings, resp)

        with pytest.raises(AuthenticationError) as exc:
            client._password_grant_with(username="u", password="p")

        assert "Requested scopes:" not in str(exc.value)

    def test_refresh_grant_sends_no_scope(self, monkeypatch):
        """The refresh token replays its granted scopes; a scope here could
        only narrow them, and a wider set is an error."""
        settings = _settings(environment="staging")
        resp = _Resp(200, {"access_token": "t", "expires_in": 3600})
        client, sent = self._client(monkeypatch, settings, resp)
        client._store_token = lambda payload: payload

        client._refresh_token("rt")

        assert "scope" not in sent
