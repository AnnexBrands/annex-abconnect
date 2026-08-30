"""Claim decoding for the bearer token the SDK sends.

The SDK reads ``role`` and ``partnerIds`` off the access token so it can
reject a payload the API would reject anyway, one round trip earlier. Two
things have to hold for that to be safe:

1. Both claims arrive as a scalar when the user has one value and as an
   array when they have several, so every consumer must see a tuple either
   way.
2. Corporate status comes from the *role*. ``CorporateAdmin`` and
   ``CorporateAccounting`` intentionally carry no ``partnerIds``, but so
   does any token whose claim is missing for an unrelated reason — reading
   corporate-ness out of an empty ``partner_ids`` would silently misroute
   ordinary users into the corporate branch.
"""

from __future__ import annotations

import base64
import json

import pytest

from ab.auth.claims import (
    CORPORATE_ROLES,
    BearerClaims,
    decode_jwt_payload,
    is_corporate_role,
)


def _jwt(payload: dict) -> str:
    """Build an unsigned JWT carrying *payload*.

    The signature is deliberately garbage: nothing in the SDK verifies it,
    and a test that supplied a real one would be asserting the wrong thing.
    """
    def _segment(obj: dict) -> str:
        raw = json.dumps(obj).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{_segment({'alg': 'RS256', 'typ': 'JWT'})}.{_segment(payload)}.not-a-signature"


class TestClaimNormalisation:
    def test_scalar_role_becomes_a_one_element_tuple(self):
        claims = BearerClaims.from_token(_jwt({"role": "PlatformUser", "partnerIds": 42}))

        assert claims.roles == ("PlatformUser",)
        assert claims.partner_ids == (42,)

    def test_list_role_is_preserved_in_order(self):
        claims = BearerClaims.from_token(
            _jwt({"role": ["PlatformUser", "Admin"], "partnerIds": [42, 43]})
        )

        assert claims.roles == ("PlatformUser", "Admin")
        assert claims.partner_ids == (42, 43)

    def test_scalar_and_list_claims_agree_on_the_single_value_case(self):
        scalar = BearerClaims.from_token(_jwt({"role": "PlatformUser", "partnerIds": 42}))
        listed = BearerClaims.from_token(_jwt({"role": ["PlatformUser"], "partnerIds": [42]}))

        assert scalar.roles == listed.roles
        assert scalar.partner_ids == listed.partner_ids

    def test_partner_ids_are_coerced_from_strings(self):
        """IdentityServer serialises every claim value as a string."""
        claims = BearerClaims.from_token(_jwt({"role": "PlatformUser", "partnerIds": ["42", "43"]}))

        assert claims.partner_ids == (42, 43)

    def test_unparseable_partner_id_is_dropped_with_a_warning(self, caplog):
        with caplog.at_level("WARNING"):
            claims = BearerClaims.from_token(_jwt({"partnerIds": ["42", {"nested": 1}]}))

        assert claims.partner_ids == (42,)
        assert "partnerIds" in caplog.text

    def test_missing_claims_yield_empty_tuples(self):
        claims = BearerClaims.from_token(_jwt({"sub": "abc"}))

        assert claims.roles == ()
        assert claims.partner_ids == ()

    def test_long_form_role_claim_is_read(self):
        """ASP.NET Core maps ``role`` from the WS-Federation claim type."""
        uri = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
        claims = BearerClaims.from_token(_jwt({uri: ["CorporateAdmin"]}))

        assert claims.roles == ("CorporateAdmin",)
        assert claims.is_corporate is True

    def test_full_payload_is_kept_for_claims_the_sdk_does_not_model(self):
        claims = BearerClaims.from_token(_jwt({"role": "PlatformUser", "sub": "user-1"}))

        assert claims.payload["sub"] == "user-1"


class TestCorporateDetection:
    @pytest.mark.parametrize("role", sorted(CORPORATE_ROLES))
    def test_corporate_roles_are_corporate_with_no_partner_ids(self, role):
        """Both corporate roles intentionally carry no ``partnerIds``."""
        claims = BearerClaims.from_token(_jwt({"role": role}))

        assert claims.roles == (role,)
        assert claims.partner_ids == ()
        assert claims.is_corporate is True

    @pytest.mark.parametrize("role", sorted(CORPORATE_ROLES))
    def test_corporate_role_among_others_still_counts(self, role):
        claims = BearerClaims.from_token(_jwt({"role": ["Admin", role]}))

        assert claims.is_corporate is True

    def test_role_matching_ignores_case(self):
        claims = BearerClaims.from_token(_jwt({"role": "corporateadmin"}))

        assert claims.is_corporate is True

    def test_non_corporate_user_with_partner_ids_is_not_corporate(self):
        claims = BearerClaims.from_token(_jwt({"role": "PlatformUser", "partnerIds": [42]}))

        assert claims.is_corporate is False

    def test_missing_partner_ids_alone_does_not_make_a_user_corporate(self):
        """The regression this guards: inferring the role from the claim's absence."""
        claims = BearerClaims.from_token(_jwt({"role": "PlatformUser"}))

        assert claims.partner_ids == ()
        assert claims.is_corporate is False

    def test_a_token_with_no_role_at_all_is_not_corporate(self):
        claims = BearerClaims.from_token(_jwt({"sub": "abc"}))

        assert claims.is_corporate is False

    def test_is_corporate_role_helper_accepts_scalar_and_list(self):
        assert is_corporate_role("CorporateAccounting") is True
        assert is_corporate_role(["Admin", "CorporateAdmin"]) is True
        assert is_corporate_role("PlatformUser") is False
        assert is_corporate_role(None) is False


class TestMalformedTokens:
    @pytest.mark.parametrize(
        "token",
        ["", "not-a-jwt", "only.two", "header.!!!not-base64!!!.sig"],
        ids=["empty", "no-dots", "two-segments", "undecodable-payload"],
    )
    def test_unreadable_tokens_degrade_to_empty_claims(self, token):
        """An unreadable token must mean *unknown*, never *corporate*."""
        claims = BearerClaims.from_token(token)

        assert claims.roles == ()
        assert claims.partner_ids == ()
        assert claims.is_corporate is False

    def test_payload_that_is_not_an_object_is_ignored(self):
        segment = base64.urlsafe_b64encode(b'["not", "an", "object"]').decode().rstrip("=")

        assert decode_jwt_payload(f"header.{segment}.sig") == {}

    def test_unpadded_payload_still_decodes(self):
        """Compact JWTs strip base64 padding; the decoder must add it back."""
        token = _jwt({"role": "PlatformUser", "partnerIds": [1]})
        assert "=" not in token.split(".")[1]

        assert BearerClaims.from_token(token).roles == ("PlatformUser",)


class TestDescribe:
    def test_describe_reports_shape_without_identifiers(self):
        claims = BearerClaims.from_token(
            _jwt({"role": "PlatformUser", "partnerIds": [42, 43], "sub": "user-1"})
        )

        described = claims.describe()

        assert described == {
            "roles": ["PlatformUser"],
            "is_corporate": False,
            "partner_id_count": 2,
        }
        assert "42" not in str(described)
        assert "user-1" not in str(described)
