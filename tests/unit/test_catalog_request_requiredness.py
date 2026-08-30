"""Which catalog request fields are required, and which default to a list.

Swagger under-declares the bulk surface: it marks properties nullable that
the API source requires, which is how a payload can validate locally and
still come back 400. These tests pin the source-proven shape.

Two rules are being enforced here, and they are different:

- **required** — the field has no default, so a payload missing it fails
  before the request goes out;
- **empty-list default** — the field is a collection, so "none of them" is
  ``[]`` and never ``None``. There is no third state to model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ab.api.models.catalog import (
    AddCatalogRequest,
    BulkUpsertCatalogRequest,
    BulkUpsertLotRequest,
    BulkUpsertRequest,
    BulkUpsertSellerRequest,
    UpdateCatalogRequest,
)
from ab.api.models.platforms import CatalogPlatformDto

BULK_CATALOG_REQUIRED = (
    "customer_catalog_id", "title", "start_date", "end_date", "platform_id", "seller",
)
BULK_LOT_REQUIRED = ("customer_item_id", "lot_number", "data")
BULK_SELLER_REQUIRED = ("name", "customer_display_id", "is_active")


def _seller() -> dict:
    return {"name": "Seller", "customerDisplayId": 123, "isActive": True}


def _lot() -> dict:
    return {"customerItemId": "ITEM-001", "lotNumber": "1", "data": {"Qty": 1}}


def _catalog() -> dict:
    return {
        "customerCatalogId": "CAT-001",
        "title": "Auction",
        "startDate": "2026-05-19T00:00:00Z",
        "endDate": "2026-05-20T00:00:00Z",
        "platformId": 11,
        "seller": _seller(),
    }


def _assert_required(model_cls, field_name: str, valid: dict) -> None:
    """A payload missing *field_name* must fail, naming that field."""
    assert model_cls.model_fields[field_name].is_required()

    alias = model_cls.model_fields[field_name].alias or field_name
    incomplete = {k: v for k, v in valid.items() if k != alias}

    with pytest.raises(ValidationError) as excinfo:
        model_cls.model_validate(incomplete)

    assert any(error["loc"] == (alias,) for error in excinfo.value.errors())


class TestBulkUpsertCatalogRequiredness:
    @pytest.mark.parametrize("field_name", BULK_CATALOG_REQUIRED)
    def test_required_field(self, field_name):
        _assert_required(BulkUpsertCatalogRequest, field_name, _catalog())

    def test_a_complete_catalog_validates(self):
        assert BulkUpsertCatalogRequest.model_validate(_catalog()).title == "Auction"

    def test_lots_defaults_to_an_empty_list(self):
        assert BulkUpsertCatalogRequest.model_validate(_catalog()).lots == []

    def test_lots_may_not_be_null(self):
        with pytest.raises(ValidationError):
            BulkUpsertCatalogRequest.model_validate({**_catalog(), "lots": None})


class TestBulkUpsertLotRequiredness:
    @pytest.mark.parametrize("field_name", BULK_LOT_REQUIRED)
    def test_required_field(self, field_name):
        _assert_required(BulkUpsertLotRequest, field_name, _lot())

    def test_image_links_defaults_to_an_empty_list(self):
        assert BulkUpsertLotRequest.model_validate(_lot()).image_links == []

    def test_image_links_may_not_be_null(self):
        with pytest.raises(ValidationError):
            BulkUpsertLotRequest.model_validate({**_lot(), "imageLinks": None})


class TestBulkUpsertSellerRequiredness:
    @pytest.mark.parametrize("field_name", BULK_SELLER_REQUIRED)
    def test_required_field(self, field_name):
        _assert_required(BulkUpsertSellerRequest, field_name, _seller())

    def test_name_is_no_longer_nullable(self):
        with pytest.raises(ValidationError):
            BulkUpsertSellerRequest.model_validate({**_seller(), "name": None})


class TestCollectionDefaults:
    def test_top_level_catalogs_defaults_to_an_empty_list(self):
        assert BulkUpsertRequest().catalogs == []

    def test_top_level_catalogs_may_not_be_null(self):
        with pytest.raises(ValidationError):
            BulkUpsertRequest.model_validate({"catalogs": None})

    def test_agent_company_ids_defaults_to_an_empty_list(self):
        request = AddCatalogRequest.model_validate({
            "title": "Auction",
            "startDate": "2026-05-19T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z",
            "isCompleted": False,
            "sellerId": 2,
        })

        assert request.agent_company_ids == []
        assert request.platforms == []

    @pytest.mark.parametrize("field_name", ["agentCompanyIds", "platforms"])
    def test_catalog_collections_may_not_be_null(self, field_name):
        with pytest.raises(ValidationError):
            AddCatalogRequest.model_validate({
                "title": "Auction",
                "startDate": "2026-05-19T00:00:00Z",
                "endDate": "2026-05-20T00:00:00Z",
                "isCompleted": False,
                "sellerId": 2,
                field_name: None,
            })

    def test_empty_defaults_are_not_sent_on_the_wire(self):
        """``check`` excludes unset fields, so a default adds nothing to the body."""
        payload = AddCatalogRequest.check({
            "title": "Auction",
            "startDate": "2026-05-19T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z",
            "isCompleted": False,
            "sellerId": 2,
        })

        assert "agentCompanyIds" not in payload
        assert "platforms" not in payload


class TestAddCatalogTitle:
    def test_title_is_required(self):
        _assert_required(AddCatalogRequest, "title", {
            "title": "Auction",
            "startDate": "2026-05-19T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z",
            "isCompleted": False,
            "sellerId": 2,
        })

    def test_update_inherits_the_requirement(self):
        assert UpdateCatalogRequest.model_fields["title"].is_required()


class TestCatalogPlatformAssociation:
    def test_platform_catalog_id_is_required(self):
        assert CatalogPlatformDto.model_fields["platform_catalog_id"].is_required()

        with pytest.raises(ValidationError) as excinfo:
            CatalogPlatformDto.model_validate({"platformId": 7})

        assert excinfo.value.errors()[0]["loc"] == ("platformCatalogId",)

    def test_a_complete_association_validates(self):
        association = CatalogPlatformDto.model_validate(
            {"platformId": 7, "platformCatalogId": "CAT-001"}
        )

        assert association.platform_catalog_id == "CAT-001"

    def test_a_catalog_supplying_a_platform_must_supply_its_external_id(self):
        with pytest.raises(ValidationError) as excinfo:
            AddCatalogRequest.model_validate({
                "title": "Auction",
                "startDate": "2026-05-19T00:00:00Z",
                "endDate": "2026-05-20T00:00:00Z",
                "isCompleted": False,
                "sellerId": 2,
                "platforms": [{"platformId": 7}],
            })

        assert excinfo.value.errors()[0]["loc"] == ("platforms", 0, "platformCatalogId")

    def test_supplying_no_platforms_at_all_stays_valid(self):
        request = AddCatalogRequest.model_validate({
            "title": "Auction",
            "startDate": "2026-05-19T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z",
            "isCompleted": False,
            "sellerId": 2,
        })

        assert request.platforms == []
