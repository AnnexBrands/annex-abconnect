"""Forced token refresh: ``HttpClient.refresh`` and the ``ab token`` command."""

from __future__ import annotations

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

from ab.auth.base import Token
from ab.auth.memory import MemoryTokenStorage
from ab.cli.__main__ import main
from ab.config import ABConnectSettings
from ab.exceptions import AuthenticationError
from ab.http import HttpClient


def _settings() -> ABConnectSettings:
    env = {
        "ABCONNECT_USERNAME": "u",
        "ABCONNECT_PASSWORD": "p",
        "ABCONNECT_CLIENT_ID": "c",
        "ABCONNECT_CLIENT_SECRET": "s",
    }
    with patch.dict(os.environ, env, clear=False):
        return ABConnectSettings()


def _ok(access_token: str) -> MagicMock:
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = {"access_token": access_token, "refresh_token": "r2", "expires_in": 3600}
    return resp


class TestHttpClientRefresh:
    def test_refreshes_even_when_token_is_valid(self):
        storage = MemoryTokenStorage(Token("old", refresh_token="r1", expires_at=time.time() + 3600))
        client = HttpClient("https://example.com/api", _settings(), storage)
        with patch("ab.http.requests.post", return_value=_ok("new")) as post:
            token = client.refresh()
        assert token.access_token == "new"
        assert storage.get_token().access_token == "new"
        assert post.call_args.kwargs["data"]["grant_type"] == "refresh_token"
        assert post.call_args.kwargs["data"]["refresh_token"] == "r1"

    def test_falls_back_to_password_grant_without_refresh_token(self):
        storage = MemoryTokenStorage()
        client = HttpClient("https://example.com/api", _settings(), storage)
        with patch("ab.http.requests.post", return_value=_ok("pw")) as post:
            token = client.refresh()
        assert token.access_token == "pw"
        assert post.call_args.kwargs["data"]["grant_type"] == "password"

    def test_no_refresh_token_and_no_fallback_raises(self):
        client = HttpClient(
            "https://example.com/api", _settings(), MemoryTokenStorage(), allow_password_fallback=False
        )
        with pytest.raises(AuthenticationError):
            client.refresh()


class TestTokenCommand:
    def test_prints_refreshed_access_token(self, capsys):
        api = MagicMock()
        api.refresh_token.return_value = Token("fresh-token")
        with patch.object(sys, "argv", ["ab", "token"]), patch(
            "ab.cli.__main__._create_api", return_value=api
        ) as create, pytest.raises(SystemExit) as exc:
            main(env="staging")
        assert exc.value.code == 0
        create.assert_called_once_with("staging")
        assert capsys.readouterr().out == "fresh-token\n"

    def test_refresh_failure_exits_2_with_stderr(self, capsys):
        api = MagicMock()
        api.refresh_token.side_effect = AuthenticationError("nope")
        with patch.object(sys, "argv", ["ab", "token"]), patch(
            "ab.cli.__main__._create_api", return_value=api
        ), pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "nope" in captured.err
