"""Bearer-token claim decoding for the SDK's own preflight checks.

The SDK reads a handful of claims out of the access token so it can catch
a payload the API would reject before spending a round trip on it — see
:func:`~ab.api.models.catalog.check_bulk_upsert`, which needs to know
whether the bearer is a corporate user.

**No signature verification happens here, and none is wanted.** The token
was minted by the IdentityServer for this client and is only ever read to
shape a request the API validates again for real. Nothing security-bearing
is decided from these claims; they are a hint that turns a 400 into a
local :class:`pydantic.ValidationError`.

Two claim shapes have to be normalised. IdentityServer emits a JSON array
when a user has several values for a claim and a bare scalar when they
have exactly one, so ``role`` and ``partnerIds`` arrive as either
``"CorporateAdmin"`` or ``["CorporateAdmin", "Admin"]``. Every consumer
here sees a tuple.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)

#: Roles whose users act across every partner rather than for one of them.
#: Per the API owner these roles intentionally carry **no** ``partnerIds``,
#: which is why corporate status is decided from the role and never from an
#: empty ``partner_ids`` — a non-corporate token with a missing claim would
#: otherwise be misread as corporate and sent down the wrong branch.
CORPORATE_ROLES: frozenset[str] = frozenset({"CorporateAdmin", "CorporateAccounting"})

_CORPORATE_ROLES_CI = frozenset(r.casefold() for r in CORPORATE_ROLES)

#: ``role`` as IdentityServer emits it, plus the long-form WS-Federation claim
#: type ASP.NET Core maps it from. Whichever appears first wins.
_ROLE_CLAIMS = (
    "role",
    "roles",
    "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
)

_PARTNER_IDS_CLAIM = "partnerIds"


def _as_tuple(value: Any) -> tuple[Any, ...]:
    """Normalise a claim that may be a scalar, a list, or absent."""
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(v for v in value if v is not None)
    return (value,)


def _as_int_tuple(value: Any, *, claim: str) -> tuple[int, ...]:
    """Normalise a numeric claim, dropping (and logging) values that are not."""
    ints: list[int] = []
    for item in _as_tuple(value):
        try:
            ints.append(int(item))
        except (TypeError, ValueError):
            logger.warning(
                "Ignoring non-integer value in the %r claim: %r", claim, type(item).__name__
            )
    return tuple(ints)


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Return the decoded payload of *token* without verifying its signature.

    Args:
        token: A compact-serialisation JWT (``header.payload.signature``).

    Returns:
        The payload as a dict. An unparseable token yields ``{}`` rather than
        raising — a claim the SDK cannot read must degrade to "unknown", never
        break an otherwise valid call.
    """
    parts = token.split(".")
    if len(parts) < 2:
        logger.warning("Bearer token is not a JWT (%d segments); no claims read", len(parts))
        return {}
    segment = parts[1]
    padding = "=" * (-len(segment) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(segment + padding))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        logger.warning("Bearer token payload is not decodable JSON; no claims read")
        return {}
    if not isinstance(payload, dict):
        logger.warning("Bearer token payload is not a JSON object; no claims read")
        return {}
    return payload


@dataclass(frozen=True)
class BearerClaims:
    """The claims the SDK reads out of an access token.

    Attributes:
        roles: Every value of the ``role`` claim, normalised to a tuple
            whether the token carried a scalar or an array.
        partner_ids: Every value of the ``partnerIds`` claim, likewise
            normalised. Empty for corporate users, who have no partner
            scoping — and also empty for a token that simply omits the
            claim, which is why it must not be used to infer a role.
        payload: The full decoded payload, for callers that need a claim
            this class does not model.
    """

    roles: tuple[str, ...] = ()
    partner_ids: tuple[int, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BearerClaims":
        """Build claims from an already-decoded JWT payload."""
        roles: tuple[str, ...] = ()
        for claim in _ROLE_CLAIMS:
            if claim in payload:
                roles = tuple(str(r) for r in _as_tuple(payload[claim]))
                break
        return cls(
            roles=roles,
            partner_ids=_as_int_tuple(payload.get(_PARTNER_IDS_CLAIM), claim=_PARTNER_IDS_CLAIM),
            payload=payload,
        )

    @classmethod
    def from_token(cls, token: str) -> "BearerClaims":
        """Build claims straight from an access token."""
        return cls.from_payload(decode_jwt_payload(token))

    @property
    def is_corporate(self) -> bool:
        """Whether the bearer holds a corporate role.

        Decided **only** from :attr:`roles`. Corporate tokens carry no
        ``partnerIds``, but so does any token whose claim is missing for an
        unrelated reason, so the absence of partner IDs proves nothing.
        """
        return any(role.casefold() in _CORPORATE_ROLES_CI for role in self.roles)

    def describe(self) -> dict[str, Any]:
        """A log-safe summary: shapes and role names, no identifiers.

        Partner IDs are reduced to a count — the SDK logs the *shape* of a
        token, never anything that identifies the bearer or the tenant.
        """
        return {
            "roles": list(self.roles),
            "is_corporate": self.is_corporate,
            "partner_id_count": len(self.partner_ids),
        }


def is_corporate_role(roles: Optional[Sequence[str] | str]) -> bool:
    """Whether any of *roles* is a corporate role. Accepts a scalar or a list."""
    return any(str(r).casefold() in _CORPORATE_ROLES_CI for r in _as_tuple(roles))
