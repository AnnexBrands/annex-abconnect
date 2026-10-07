"""Unified HTTP client for all ABConnect API surfaces.

Wraps :class:`requests.Session` with connection pooling, Bearer JWT
injection, timeout enforcement, and retry with exponential backoff for
transient errors (429, 502, 503).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Mapping, Optional, Union

import requests

from ab.auth.base import Token, TokenStorage
from ab.auth.claims import BearerClaims
from ab.config import ABConnectSettings
from ab.exceptions import AuthenticationError, RequestError

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 502, 503}
_TOKEN_EXPIRY_BUFFER = 300  # seconds


class HttpClient:
    """Low-level HTTP transport shared by all endpoint classes.

    A single :class:`HttpClient` is created per API surface (ACPortal,
    Catalog, ABC) and owns a :class:`requests.Session` for connection
    pooling.
    """

    def __init__(
        self,
        base_url: str,
        settings: ABConnectSettings,
        token_storage: TokenStorage,
        *,
        allow_password_fallback: bool = True,
        extra_headers: Optional[Union[Dict[str, str], Callable[[], Dict[str, str]]]] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._settings = settings
        self._token_storage = token_storage
        self._session = requests.Session()
        self._allow_password_fallback = allow_password_fallback
        self._extra_headers = extra_headers
        self._claims_cache: Optional[tuple[str, BearerClaims]] = None

    @property
    def environment(self) -> str:
        """The environment this client targets (``"staging"`` or ``"production"``)."""
        return self._settings.environment

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _ensure_token(self) -> Token:
        """Return a valid access token, authenticating or refreshing as needed."""
        token = self._token_storage.get_token()

        if token and not token.expired:
            return token

        # Try refresh first
        if token and token.refresh_token:
            refreshed = self._refresh_token(token.refresh_token)
            if refreshed:
                return refreshed

        if not self._allow_password_fallback:
            if token is not None:
                self._token_storage.clear_token()
            raise AuthenticationError("No valid ABConnect token is available for this session")

        # Fall back to password grant
        return self._password_grant()

    def refresh(self) -> Token:
        """Force a new access token, even if the stored one is still valid.

        Exchanges the stored refresh token; if there is none or the exchange
        fails, falls back to a password grant (when this client allows it).
        """
        token = self._token_storage.get_token()
        if token and token.refresh_token:
            refreshed = self._refresh_token(token.refresh_token)
            if refreshed:
                return refreshed
        if not self._allow_password_fallback:
            raise AuthenticationError("No refresh token is available for this session")
        return self._password_grant()

    def _password_grant(self) -> Token:
        return self._password_grant_with(
            username=self._settings.username,
            password=self._settings.password,
        )

    def _password_grant_with(self, *, username: str, password: str) -> Token:
        """Password grant using caller-supplied credentials."""
        if not username or not password:
            raise AuthenticationError("Password grant requires username and password")
        scope = self._settings.oauth_scopes
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
            "scope": scope,
        }
        resp = requests.post(self._settings.identity_url, data=data, timeout=self._settings.timeout)
        if not resp.ok:
            raise AuthenticationError(self._login_failure_message(username, resp, scope))
        return self._store_token(resp.json())

    def _login_failure_message(self, username: str, resp: "requests.Response", scope: str) -> str:
        """Explain a failed grant, spelling out scope rejections.

        The server rejects the *whole* grant with a bare ``invalid_scope`` when
        any single requested scope is not provisioned for the client, without
        saying which one -- so name the set that was asked for and where to
        change it.
        """
        base = f"Login failed for {username}: {resp.status_code} {resp.text}"
        try:
            error = resp.json().get("error")
        except ValueError:
            error = None
        if error != "invalid_scope":
            return base
        return (
            f"{base}\nRequested scopes: {scope!r}. The server rejects the entire "
            "grant when any one scope is not provisioned for client "
            f"{self._settings.client_id!r} on {self._settings.environment}. Set "
            "ABCONNECT_SCOPES (or ABConnectSettings.scopes) to the subset your "
            "client allows."
        )

    def _refresh_token(self, refresh_token: str) -> Optional[Token]:
        """Exchange a refresh token for a fresh access token.

        Deliberately sends **no** ``scope``: the refresh token already carries
        the scopes granted to it, and the server replays them in full (verified
        against staging on 2026-08-23). Passing a scope here could only narrow
        the result, and passing a *wider* set than was originally granted is an
        error.

        One consequence: changing :attr:`~ab.config.ABConnectSettings.scopes`
        takes effect at the next password grant, not the next refresh. Clear the
        stored token to apply a scope change immediately.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
        }
        try:
            resp = requests.post(self._settings.identity_url, data=data, timeout=self._settings.timeout)
            if resp.ok:
                return self._store_token(resp.json())
        except Exception:
            logger.info("Refresh token failed, will attempt password grant")
        return None

    def _store_token(self, payload: dict) -> Token:
        token = Token(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=time.time() + payload.get("expires_in", 3600) - _TOKEN_EXPIRY_BUFFER,
            token_type=payload.get("token_type", "Bearer"),
        )
        self._token_storage.save_token(token)
        return token

    def bearer_claims(self) -> Optional[BearerClaims]:
        """Return the claims carried by the bearer this client would send.

        Obtains a token exactly the way :meth:`request` does — so calling this
        before a request only moves the grant a few milliseconds earlier — and
        decodes it. The result is cached against the access token itself, so a
        refresh or a re-login invalidates it without any extra bookkeeping.

        Returns ``None`` when no token can be obtained (an ``anonymous``
        client, or storage with nothing in it and no password fallback).
        Callers must read that as *unknown*, not as any particular role.
        """
        try:
            token = self._ensure_token()
        except AuthenticationError:
            return None
        if self._claims_cache is not None and self._claims_cache[0] == token.access_token:
            return self._claims_cache[1]
        claims = BearerClaims.from_token(token.access_token)
        self._claims_cache = (token.access_token, claims)
        return claims

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        files: Optional[Mapping[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raw: bool = False,
        auth_optional: bool = False,
    ) -> Any:
        """Send an HTTP request with auth, timeout, and retry logic.

        When *auth_optional* is ``True`` and no token can be obtained, the
        request proceeds **without** an ``Authorization`` header (endpoints
        that accept body-level credentials such as an autoprice AccessKey).
        A token is still attached whenever one is available.

        Returns parsed JSON, raw bytes, ``None`` (for 204), or the raw
        :class:`requests.Response` when *raw* is ``True``.
        """
        if auth_optional:
            try:
                token = self._ensure_token()
            except AuthenticationError:
                token = None
        else:
            token = self._ensure_token()
        url = f"{self._base_url}{path}"

        req_headers: Dict[str, str] = {}
        if token is not None:
            req_headers["Authorization"] = f"Bearer {token.access_token}"
        if self._extra_headers is not None:
            client_headers = (
                self._extra_headers() if callable(self._extra_headers) else self._extra_headers
            )
            req_headers.update(client_headers or {})
        if headers:
            req_headers.update(headers)


        for attempt in range(1, self._settings.max_attempts + 1):
            logger.debug("%s %s (attempt %d)", method.upper(), url, attempt)

            try:
                resp = self._session.request(
                    method=method.upper(),
                    url=url,
                    headers=req_headers,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    timeout=self._settings.timeout,
                )
            except requests.RequestException as exc:
                if attempt < self._settings.max_attempts:
                    self._backoff(attempt)
                    continue
                raise RequestError(0, str(exc)) from exc

            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < self._settings.max_attempts:
                self._backoff(attempt)
                continue

            if raw:
                return resp

            return self._handle_response(resp)

        # Should not reach here, but just in case
        raise RequestError(0, f"Request failed after {self._settings.max_attempts} attempts")

    @staticmethod
    def _backoff(attempt: int) -> None:
        delay = min(2 ** attempt, 30)
        logger.info("Retrying in %ds…", delay)
        time.sleep(delay)

    @staticmethod
    def _handle_response(resp: requests.Response) -> Any:
        if resp.status_code == 204:
            return None

        if not (200 <= resp.status_code < 300):
            try:
                error_info = resp.json()
                message = error_info.get("message", resp.text)
            except Exception:
                message = resp.text
            raise RequestError(resp.status_code, message)

        content_type = resp.headers.get("Content-Type", "").lower()
        binary_types = ("application/pdf", "application/octet-stream", "image/", "application/zip")
        if any(bt in content_type for bt in binary_types):
            return resp.content

        # A 2xx with an empty body (common for DELETE and replace-all save
        # endpoints that return 200 + no content) is success, not a JSON error.
        if not resp.content or not resp.text.strip():
            return None

        try:
            return resp.json()
        except Exception:
            raise RequestError(resp.status_code, "Response was not valid JSON")
