"""Fixture validation tests for Catalog API models.

Targets the migrated Catalog schema (staging): ``agentCompanyIds``, a singular
``seller``, per-platform external IDs, and ``itemData`` in place of
``overridenData``.
"""


from ab.api.models.catalog import (
    BulkUpsertRequest,
    CatalogDto,
    CatalogExpandedDto,
    CatalogWithLotsDto,
)
from ab.api.models.lots import (
    AddLotRequest,
    LotCatalogInformationDto,
    LotClientItemDataDto,
    LotDataDto,
    LotDto,
    LotItemDataDto,
)
from ab.api.models.platforms import CatalogPlatformDto, LotPlatformDto, PlatformDto
from ab.api.models.sellers import SellerDto, SellerExpandedDto
from tests.conftest import assert_no_extra_fields, require_fixture


class TestCatalogModels:
    def test_catalog_with_lots_dto(self):
        data = require_fixture("CatalogWithLotsDto", "GET", "/Catalog/{id}")
        model = CatalogWithLotsDto.model_validate(data)
        assert isinstance(model, CatalogWithLotsDto)
        assert_no_extra_fields(model)
        if model.seller:
            assert isinstance(model.seller, SellerDto)
        if model.lots:
            assert isinstance(model.lots[0], LotCatalogInformationDto)
        if model.platforms:
            assert isinstance(model.platforms[0], CatalogPlatformDto)

    def test_catalog_expanded_dto(self):
        data = require_fixture("CatalogExpandedDto", "PUT", "/Catalog/{id}")
        model = CatalogExpandedDto.model_validate(data)
        assert isinstance(model, CatalogExpandedDto)
        assert_no_extra_fields(model)
        if model.seller:
            assert isinstance(model.seller, SellerDto)

    def test_catalog_dto_has_no_retired_fields(self):
        """The migration retired ``customerCatalogId`` and ``agent``."""
        fields = set(CatalogDto.model_fields)
        assert "customer_catalog_id" not in fields
        assert "agent" not in fields
        assert "agent_company_ids" in fields

    def test_lot_dto(self):
        data = require_fixture("LotDto", "GET", "/Lot/{id}")
        model = LotDto.model_validate(data)
        assert isinstance(model, LotDto)
        assert_no_extra_fields(model)
        if model.platforms:
            assert isinstance(model.platforms[0], LotPlatformDto)

    def test_lot_dto_has_no_retired_fields(self):
        """The migration retired ``customerItemId`` and renamed ``overridenData``."""
        fields = set(LotDto.model_fields)
        assert "customer_item_id" not in fields
        assert "overriden_data" not in fields
        assert "item_data" in fields
        assert "platforms" in fields

    def test_lot_client_item_data_dto(self):
        data = require_fixture("LotClientItemDataDto", "POST", "/Lot/{id}/ClientItemData")
        model = LotClientItemDataDto.model_validate(data)
        assert isinstance(model, LotClientItemDataDto)
        assert_no_extra_fields(model)
        if model.client_item_data:
            assert isinstance(model.client_item_data[0], LotDataDto)

    def test_lot_item_data_dto(self):
        """``POST /Lot/ItemData`` returns an array of these.

        Staging has never returned a non-empty array for any query shape, so
        this asserts the declared swagger shape rather than a captured one —
        see the note in ``FIXTURES.md``.
        """
        model = LotItemDataDto.model_validate({
            "platformItemId": "ITEM-001",
            "initialData": {"Qty": 1, "L": 10.0},
            "itemData": [{"Qty": 2, "L": 11.0}],
        })
        assert model.platform_item_id == "ITEM-001"
        assert model.initial_data.l == 10.0
        assert model.item_data[0].qty == 2

    def test_platform_dto(self):
        data = require_fixture("PlatformDto", "GET", "/Platform/{id}")
        model = PlatformDto.model_validate(data)
        assert isinstance(model, PlatformDto)
        assert_no_extra_fields(model)

    def test_lot_data_dto(self):
        data = require_fixture("LotDataDto", "GET", "/Lot/{id}")
        model = LotDataDto.model_validate(data)
        assert isinstance(model, LotDataDto)
        assert_no_extra_fields(model)

    def test_lot_data_dto_uses_db_dimension_field_names(self):
        model = LotDataDto(l=10, w=5, h=3, wgt=2)

        assert model.l == 10
        assert model.w == 5
        assert model.h == 3
        assert model.wgt == 2
        assert not hasattr(model, "length")
        assert not hasattr(model, "width")
        assert not hasattr(model, "height")
        assert not hasattr(model, "weight")
        assert model.model_dump(by_alias=False, exclude_none=True) == {
            "l": 10,
            "w": 5,
            "h": 3,
            "wgt": 2,
        }
        assert model.model_dump(by_alias=True, exclude_none=True) == {
            "L": 10,
            "W": 5,
            "H": 3,
            "Wgt": 2,
        }

    def test_lot_data_dto_hydrates_wire_dimension_names_to_db_field_names(self):
        model = LotDataDto.model_validate({"L": 10, "W": 5, "H": 3, "Wgt": 2})

        assert model.l == 10
        assert model.w == 5
        assert model.h == 3
        assert model.wgt == 2
        assert model.model_dump(by_alias=False, exclude_none=True) == {
            "l": 10,
            "w": 5,
            "h": 3,
            "wgt": 2,
        }

    def test_lot_data_dto_ignores_long_dimension_names(self):
        model = LotDataDto(length=10, width=5, height=3, weight=2)

        assert model.l is None
        assert model.w is None
        assert model.h is None
        assert model.wgt is None
        assert model.model_dump(by_alias=False, exclude_none=True) == {}

    def test_lot_data_dto_dropped_value_field(self):
        """The migrated swagger no longer declares ``value``."""
        assert "value" not in LotDataDto.model_fields

    def test_add_lot_omits_item_data_when_not_explicitly_provided(self):
        payload = AddLotRequest.check({
            "platforms": [{"platformId": 1, "platformItemId": "ITEM-001"}],
            "catalogs": [{"catalogId": 1, "lotNumber": "1"}],
            "initialData": {"Qty": 1, "Description": "Initial dimensions only"},
        })

        assert payload["initialData"] == {"Qty": 1, "description": "Initial dimensions only"}
        assert "itemData" not in payload

    def test_add_lot_sends_item_data_when_explicitly_provided(self):
        payload = AddLotRequest.check({
            "platforms": [{"platformId": 1, "platformItemId": "ITEM-001"}],
            "initialData": {"Qty": 1},
            "itemData": [{"Qty": 1, "Description": "Explicit override"}],
        })

        assert payload["itemData"] == [{"Qty": 1, "description": "Explicit override"}]

    def test_bulk_upsert_nests_a_single_seller_per_catalog(self):
        payload = BulkUpsertRequest.check({
            "catalogs": [
                {
                    "customerCatalogId": "CAT-001",
                    "title": "Auction",
                    "startDate": "2026-05-19T00:00:00Z",
                    "endDate": "2026-05-20T00:00:00Z",
                    "lots": [
                        {
                            "customerItemId": "ITEM-001",
                            "lotNumber": "1",
                            "data": {"Qty": 1, "Description": "Bulk dimensions"},
                        },
                    ],
                    "seller": {"name": "Seller", "customerDisplayId": 123, "isActive": True},
                },
            ],
        })

        catalog_payload = payload["catalogs"][0]
        assert catalog_payload["seller"] == {
            "name": "Seller",
            "customerDisplayId": 123,
            "isActive": True,
        }
        assert catalog_payload["lots"][0]["data"] == {
            "Qty": 1,
            "description": "Bulk dimensions",
        }
        # The retired flat identity fields are gone from the catalog DTOs, but
        # bulk still matches incoming rows on the caller's own identifiers.
        assert catalog_payload["customerCatalogId"] == "CAT-001"
        assert catalog_payload["lots"][0]["customerItemId"] == "ITEM-001"

    def test_seller_dto(self):
        data = require_fixture("SellerDto", "GET", "/Seller/{id}", required=True)
        model = SellerDto.model_validate(data)
        assert isinstance(model, SellerDto)
        assert_no_extra_fields(model)

    def test_seller_expanded_dto(self):
        data = require_fixture("SellerExpandedDto", "GET", "/Seller/{id}", required=True)
        # Fixture may be a paginated wrapper {items, pageNumber, ...}
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
            assert len(items) > 0, "SellerExpandedDto fixture has empty items array"
            data = items[0]
        model = SellerExpandedDto.model_validate(data)
        assert isinstance(model, SellerExpandedDto)
        assert_no_extra_fields(model)
        if model.catalogs:
            assert isinstance(model.catalogs[0], CatalogDto)
