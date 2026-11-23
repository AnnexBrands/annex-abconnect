"""The client's partner: token claim for partner logins, configuration for corporate ones."""

import base64
import json
from unittest.mock import MagicMock

import pytest

from ab.api.endpoints.lots import LotsEndpoint
from ab.auth.base import Token
from ab.config import ABConnectSettings
from ab.exceptions import ConfigurationError
from ab.http import HttpClient


def _jwt(payload: dict) -> str:
    def segment(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{segment({'alg': 'none'})}.{segment(payload)}.synthetic"


def _client(claims: dict, partner_id=None) -> HttpClient:
    settings = ABConnectSettings(
        client_id="synthetic", client_secret="synthetic", require_credentials=False, partner_id=partner_id
    )
    client = HttpClient("https://example.invalid/api", settings, MagicMock(), allow_password_fallback=False)
    client._ensure_token = lambda: Token(access_token=_jwt(claims), expires_at=4102444800)
    return client


CORPORATE = {"role": "CorporateAccounting"}
PARTNER = {"role": "Admin", "partnerIds": "5"}
TWO_PARTNERS = {"role": "Admin", "partnerIds": ["5", "7"]}


def test_a_partner_login_takes_its_partner_from_the_token():
    assert _client(PARTNER).resolve_partner_id() == 5
    assert _client(PARTNER, partner_id=5).resolve_partner_id() == 5


def test_a_corporate_login_needs_a_configured_partner():
    assert _client(CORPORATE, partner_id=1).resolve_partner_id() == 1
    with pytest.raises(ConfigurationError, match="ABCONNECT_PARTNER_ID"):
        _client(CORPORATE).resolve_partner_id()


def test_a_configured_partner_that_contradicts_the_token_is_an_error():
    with pytest.raises(ConfigurationError, match=r"partner_id 1 is configured.*\[5\]"):
        _client(PARTNER, partner_id=1).resolve_partner_id()


def test_a_login_with_several_partners_must_choose():
    with pytest.raises(ConfigurationError, match="belongs to 2 partners"):
        _client(TWO_PARTNERS).resolve_partner_id()
    assert _client(TWO_PARTNERS, partner_id=7).resolve_partner_id() == 7


def test_the_setting_reads_from_the_environment(monkeypatch):
    monkeypatch.setenv("ABCONNECT_PARTNER_ID", "9")
    settings = ABConnectSettings(client_id="synthetic", client_secret="synthetic", require_credentials=False)
    assert settings.partner_id == 9


def test_item_data_fills_an_omitted_partner_and_keeps_an_explicit_one():
    client = MagicMock()
    client.resolve_partner_id.return_value = 5
    client.request.return_value = []
    LotsEndpoint(client).item_data(data={"customer_item_ids": ["synthetic"]})
    assert client.request.call_args.kwargs["json"] == {"partnerId": 5, "customerItemIds": ["synthetic"]}
    client.reset_mock()
    LotsEndpoint(client).item_data(data={"partner_id": 1, "customer_item_ids": ["synthetic"]})
    assert client.request.call_args.kwargs["json"]["partnerId"] == 1
    client.resolve_partner_id.assert_not_called()


def test_item_data_without_any_partner_fails_before_the_request():
    client = MagicMock()
    client.resolve_partner_id.side_effect = ConfigurationError("no partner")
    with pytest.raises(ConfigurationError):
        LotsEndpoint(client).item_data(data={"customer_item_ids": ["synthetic"]})
    client.request.assert_not_called()


def test_reading_the_client_partner_attribute_is_side_effect_free(monkeypatch):
    from ab import ABConnectAPI

    for name in ("ABCONNECT_PARTNER_ID", "ABCONNECT_USERNAME", "ABCONNECT_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ABCONNECT_CLIENT_ID", "synthetic")
    monkeypatch.setenv("ABCONNECT_CLIENT_SECRET", "synthetic")
    monkeypatch.chdir("/")
    api = ABConnectAPI(anonymous=True)
    api._catalog._ensure_token = lambda: pytest.fail("reading partner_id must not obtain a token")
    assert api.partner_id is None
    assert hasattr(api, "partner_id")
    assert ABConnectAPI(anonymous=True, partner_id=5).partner_id == 5
    assert callable(api.resolve_partner_id)


def test_explicit_settings_ignore_the_process_environment_and_env_files(monkeypatch, tmp_path):
    from ab import ABConnectAPI
    from ab.auth.memory import MemoryTokenStorage

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ABCONNECT_USERNAME=from-file\nABCONNECT_PARTNER_ID=3\n")
    env = {"USERNAME": "from-env", "PASSWORD": "x", "CLIENT_ID": "env-client", "ENVIRONMENT": "production"}
    for name, value in env.items():
        monkeypatch.setenv(f"ABCONNECT_{name}", value)

    def settings(user):
        return ABConnectSettings.explicit(
            environment="staging", username=user, password="synthetic", client_id="synthetic", client_secret="synthetic"
        )

    one = ABConnectAPI(settings=settings("partner-a"), token_storage=MemoryTokenStorage(), partner_id=5)
    two = ABConnectAPI(settings=settings("partner-b"), token_storage=MemoryTokenStorage())
    assert (one._settings.username, one._settings.environment, one.partner_id) == ("partner-a", "staging", 5)
    assert (two._settings.username, two._settings.client_id, two.partner_id) == ("partner-b", "synthetic", None)
    assert one._catalog._base_url.startswith("https://catalog-api.staging.")
    with pytest.raises(ValueError, match="either settings= or env="):
        ABConnectAPI(settings=settings("partner-a"), env="staging")
    with pytest.raises(TypeError):
        ABConnectSettings.explicit(username="no-environment")
