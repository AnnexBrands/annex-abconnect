"""``platformId`` on bulk upsert: required of every caller.

``BulkUpsertCatalogRequest.platformId`` is a real JSON property that never
appears in swagger — the API declares it ``[SwaggerIgnore]``, which hides it
from the generated document and changes nothing about the binder.

The API's own rule is conditional: corporate users (``CorporateAdmin``,
``CorporateAccounting``) must send it, because their tokens intentionally
carry no ``partnerIds`` claim to resolve a platform from, while non-corporate
users may omit it and be resolved through theirs. **The SDK is deliberately
stricter and requires it of everyone**, so one payload shape works for every
caller and the intended platform is recorded in the body.

What the API does with the value is a separate matter, and worth knowing:
verified against staging on 2026-08-28, it is authoritative only for corporate
bearers and *ignored* for everyone else — a platform user on partner 1 who
names platform 15 is silently given platform 11 with a ``200``. That is the
API's behaviour, not the SDK's, so nothing here asserts it; see
``scripts/verify_platform_id_live.py``.

That makes the model itself the enforcement point: a missing ``platformId``
fails in ``BulkUpsertRequest.check`` — which ``BaseEndpoint._request`` runs
*before* it touches the transport — so the failure costs no HTTP call and
needs no knowledge of the bearer.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from ab.api.endpoints.catalog import CatalogEndpoint
from ab.api.models.catalog import BulkUpsertCatalogRequest, BulkUpsertRequest


def _catalog(**overrides) -> dict:
    """A minimal valid catalog entry — every required field, nothing more."""
    catalog = {
        "customerCatalogId": "CAT-001",
        "title": "Auction",
        "startDate": "2026-05-19T00:00:00Z",
        "endDate": "2026-05-20T00:00:00Z",
        "platformId": 11,
        "seller": {"name": "Seller", "customerDisplayId": 123, "isActive": True},
    }
    catalog.update(overrides)
    return catalog


def _without(catalog: dict, key: str) -> dict:
    return {k: v for k, v in catalog.items() if k != key}


class _RecordingClient:
    """HttpClient stand-in that records calls and answers with a catalog."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return [{
            "id": 1,
            "startDate": "2026-05-19T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z",
            "isCompleted": False,
        }]


class TestPlatformIdField:
    def test_platform_id_is_required_and_camel_cased(self):
        field = BulkUpsertCatalogRequest.model_fields["platform_id"]

        assert field.is_required()
        assert field.alias == "platformId"

    def test_platform_id_serializes_under_its_alias(self):
        payload = BulkUpsertRequest.check({"catalogs": [_catalog(platformId=7)]})

        assert payload["catalogs"][0]["platformId"] == 7
        assert "platform_id" not in payload["catalogs"][0]

    def test_platform_id_accepts_the_snake_case_name_too(self):
        payload = BulkUpsertRequest.check(
            {"catalogs": [_without(_catalog(), "platformId") | {"platform_id": 7}]}
        )

        assert payload["catalogs"][0]["platformId"] == 7

    def test_platform_id_survives_a_model_instance_round_trip(self):
        request = BulkUpsertRequest.model_validate({"catalogs": [_catalog(platformId=15)]})

        assert request.catalogs[0].platform_id == 15
        assert BulkUpsertRequest.check(request)["catalogs"][0]["platformId"] == 15

    def test_platform_id_must_be_an_integer(self):
        with pytest.raises(ValidationError) as excinfo:
            BulkUpsertRequest.check({"catalogs": [_catalog(platformId="eleven")]})

        assert excinfo.value.errors()[0]["loc"] == ("catalogs", 0, "platformId")

    def test_partner_ids_is_not_a_body_field(self):
        """``partnerIds`` is a token claim. It must never appear in a body."""
        assert "partner_ids" not in BulkUpsertCatalogRequest.model_fields

        with pytest.raises(ValidationError):
            BulkUpsertRequest.check({"catalogs": [_catalog(partnerIds=[42])]})


class TestMissingPlatformId:
    def test_missing_platform_id_raises_at_the_failing_location(self):
        with pytest.raises(ValidationError) as excinfo:
            BulkUpsertRequest.check({"catalogs": [_without(_catalog(), "platformId")]})

        (error,) = excinfo.value.errors()
        assert error["loc"] == ("catalogs", 0, "platformId")
        assert error["type"] == "missing"

    def test_null_platform_id_is_rejected_rather_than_sent(self):
        with pytest.raises(ValidationError) as excinfo:
            BulkUpsertRequest.check({"catalogs": [_catalog(platformId=None)]})

        assert excinfo.value.errors()[0]["loc"] == ("catalogs", 0, "platformId")

    def test_every_offending_index_is_reported_at_once(self):
        body = {
            "catalogs": [
                _catalog(platformId=11),
                _without(_catalog(), "platformId"),
                _without(_catalog(), "platformId"),
                _catalog(platformId=15),
            ],
        }

        with pytest.raises(ValidationError) as excinfo:
            BulkUpsertRequest.check(body)

        assert [e["loc"] for e in excinfo.value.errors()] == [
            ("catalogs", 1, "platformId"),
            ("catalogs", 2, "platformId"),
        ]

    def test_an_empty_catalog_list_has_nothing_to_reject(self):
        assert BulkUpsertRequest.check({"catalogs": []}) == {"catalogs": []}


class TestEndpointBehaviour:
    def test_missing_platform_id_costs_no_http_call(self):
        client = _RecordingClient()

        with pytest.raises(ValidationError) as excinfo:
            CatalogEndpoint(client).bulk_upsert(
                data={"catalogs": [_without(_catalog(), "platformId")]}
            )

        assert excinfo.value.errors()[0]["loc"] == ("catalogs", 0, "platformId")
        assert client.calls == []

    def test_a_complete_payload_goes_out_with_its_platform_id(self):
        client = _RecordingClient()

        CatalogEndpoint(client).bulk_upsert(data={"catalogs": [_catalog(platformId=11)]})

        (method, path, kwargs) = client.calls[0]
        assert (method, path) == ("POST", "/Bulk/upsert")
        assert kwargs["json"]["catalogs"][0]["platformId"] == 11
        assert "partnerIds" not in json.dumps(kwargs["json"])

    def test_catalogs_may_name_different_platforms_in_one_payload(self):
        client = _RecordingClient()

        CatalogEndpoint(client).bulk_upsert(data={
            "catalogs": [_catalog(platformId=11), _catalog(platformId=15)],
        })

        sent = client.calls[0][2]["json"]["catalogs"]
        assert [c["platformId"] for c in sent] == [11, 15]

    def test_the_endpoint_needs_no_bearer_context(self):
        """The rule is unconditional, so a client with no auth still validates.

        The catalog surface is exercised by stubs that cannot report claims;
        requiring ``platformId`` of everyone is what keeps them working.
        """
        assert not hasattr(CatalogEndpoint, "_bearer_claims")

        client = _RecordingClient()
        CatalogEndpoint(client).bulk_upsert(data={"catalogs": [_catalog()]})

        assert client.calls[0][1] == "/Bulk/upsert"


class TestDerivingYourPlatform:
    """The recipe the docstrings point at, for a caller who must now name one."""

    def test_partner_ids_from_the_bearer_map_to_platforms(self):
        from ab.api.models.platforms import PlatformDto
        from ab.auth.claims import BearerClaims

        claims = BearerClaims.from_payload({"role": "Admin", "partnerIds": "1"})
        visible = [
            PlatformDto.model_validate({"id": 11, "name": "A", "partnerId": 1, "isActive": True}),
            PlatformDto.model_validate({"id": 15, "name": "B", "partnerId": 5, "isActive": True}),
        ]

        mine = [p.id for p in visible if p.partner_id in claims.partner_ids]

        assert mine == [11]

    def test_a_corporate_bearer_has_no_partner_to_derive_from(self):
        from ab.auth.claims import BearerClaims

        claims = BearerClaims.from_payload({"role": "CorporateAdmin"})

        assert claims.is_corporate is True
        assert claims.partner_ids == ()
