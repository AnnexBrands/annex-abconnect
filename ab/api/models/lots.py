"""Lot models for the Catalog API.

Field shapes ported against ``ab/api/schemas/catalog.json`` (swagger,
Tier 3) with ``ABConnectTools/ABConnect/api/models/catalog.py`` as
secondary reference (Tier 4). The prior placeholder implementation
had invented field names that did not match either source — see
``specs/036-lotsdb-migration-prep/gap-recommendations.md`` for the
full drift history.

**Staging schema migration.** These models target the migrated Catalog
schema, which at the time of writing is deployed to staging only. Three
changes are breaking:

- ``Lots.CustomerItemId`` is retired (``ObsoleteCustomerItemId`` in the
  database). The lot's external identity now lives per-platform on
  :class:`~ab.api.models.platforms.LotPlatformDto.platform_item_id`.
- ``overridenData`` is renamed ``itemData`` on both reads and writes.
- ``LotDataDto`` no longer declares ``value``.

Casing note: the Catalog API uses mixed PascalCase / camelCase for
``LotDataDto`` field aliases (``Qty``, ``L``, ``W``, ``H``, ``Wgt``,
``Cpack``, ``ItemID``, ``Notes`` are PascalCase; ``description``,
``forceCrate``, ``doNotTip``, ``commodityId``, ``notedConditions`` are
camelCase). Python field names keep the database shape
(``l``/``w``/``h``/``wgt``) because downstream tools diff and persist
``model_dump(by_alias=False)``. Aliases below match swagger exactly.
ABConnectTools used uniform PascalCase on writes (``CPack``); when in
doubt swagger wins per the constitution's Sources of Truth hierarchy.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, ConfigDict, Field, field_validator

from ab.api.models.base import RequestModel, ResponseModel
from ab.api.models.platforms import LotPlatformDto


class LotDataDto(ResponseModel):
    """Nested data payload shared by lot reads and writes.

    Used in both response contexts (``LotDto.initial_data``) and request
    contexts (``AddLotRequest.initial_data``, ``BulkUpsertLotRequest.data``).
    ``extra="ignore"`` is used instead of the default ``allow`` because
    the API occasionally echoes keys from related entities back into
    nested lot data.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    qty: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("Qty", "qty"),
        serialization_alias="Qty",
        description="Quantity",
    )
    l: Optional[float] = Field(  # noqa: E741 - Catalog DB/API domain field name.
        None,
        validation_alias=AliasChoices("L", "l"),
        serialization_alias="L",
        description="Length",
    )
    w: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("W", "w"),
        serialization_alias="W",
        description="Width",
    )
    h: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("H", "h"),
        serialization_alias="H",
        description="Height",
    )
    wgt: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("Wgt", "wgt"),
        serialization_alias="Wgt",
        description="Weight",
    )
    cpack: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("Cpack", "CPack", "cpack"),
        serialization_alias="Cpack",
        description="Container pack ID",
    )
    description: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("description", "Description"),
        serialization_alias="description",
        description="Item description",
    )
    force_crate: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("forceCrate", "ForceCrate"),
        serialization_alias="forceCrate",
        description="Force crating flag",
    )
    item_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("ItemID", "itemID", "itemId"),
        serialization_alias="ItemID",
        description="Item ID (string per swagger; ABConnectTools treated as int)",
    )
    notes: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("Notes", "notes"),
        serialization_alias="Notes",
        description="Free-text notes",
    )
    noted_conditions: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("notedConditions", "NotedConditions"),
        serialization_alias="notedConditions",
        description="Recorded conditions",
    )
    do_not_tip: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("doNotTip", "DoNotTip"),
        serialization_alias="doNotTip",
        description="Do-not-tip flag",
    )
    commodity_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("commodityId", "CommodityId"),
        serialization_alias="commodityId",
        description="Commodity / HS code ID (string per swagger)",
    )

    @field_validator("qty", mode="before")
    @classmethod
    def _empty_string_to_none(cls, v):  # noqa: D401
        """Coerce empty strings to None for optional int fields."""
        return None if v == "" else v


class ImageLinkDto(ResponseModel):
    """Image link reference."""

    id: int = Field(..., description="Image ID")
    link: Optional[str] = Field(None, description="Image URL")


class LotCatalogDto(ResponseModel):
    """Lot-to-catalog association. Also used as a body fragment in
    :class:`AddLotRequest` and :class:`UpdateLotRequest`."""

    catalog_id: int = Field(..., alias="catalogId", description="Parent catalog ID")
    lot_number: Optional[str] = Field(None, alias="lotNumber", description="Lot number within catalog")


class LotCatalogInformationDto(ResponseModel):
    """Basic lot information embedded in a catalog response."""

    id: int = Field(..., description="Lot ID")
    lot_number: Optional[str] = Field(None, alias="lotNumber", description="Lot number")


class LotDto(ResponseModel):
    """Full lot — returned by ``POST /Lot``, ``GET /Lot/{id}``,
    ``PUT /Lot/{id}`` and ``POST /Lot/{targetId}/merge/{sourceId}``."""

    id: int = Field(..., description="Lot ID")
    initial_data: Optional[LotDataDto] = Field(None, alias="initialData", description="Initial lot data")
    item_data: Optional[List[LotDataDto]] = Field(
        None, alias="itemData", description="Item data entries (formerly ``overridenData``)",
    )
    catalogs: Optional[List[LotCatalogDto]] = Field(
        None, description="Catalog associations (each entry is a LotCatalogDto)",
    )
    platforms: Optional[List[LotPlatformDto]] = Field(
        None, description="Platform associations carrying the lot's external IDs",
    )
    image_links: Optional[List[ImageLinkDto]] = Field(
        None, alias="imageLinks", description="Attached image links",
    )


class LotItemDataDto(ResponseModel):
    """Item data for one lot keyed by its platform item ID — an entry in
    the ``POST /Lot/ItemData`` response.

    Replaces the retired ``LotOverrideDto`` from ``POST /Lot/get-overrides``,
    which keyed on ``customerItemId``.
    """

    platform_item_id: Optional[str] = Field(
        None, alias="platformItemId", description="Platform item ID the data belongs to",
    )
    initial_data: Optional[LotDataDto] = Field(None, alias="initialData", description="Initial lot data")
    item_data: Optional[List[LotDataDto]] = Field(
        None, alias="itemData", description="Item data entries",
    )


class LotClientItemDataDto(ResponseModel):
    """A client-supplied item data record attached to a lot — returned by
    ``POST`` and ``GET /Lot/{id}/ClientItemData``."""

    id: int = Field(..., description="Client item data record ID")
    lot_id: int = Field(..., alias="lotId", description="Owning lot ID")
    client_item_data: Optional[List[LotDataDto]] = Field(
        None, alias="clientItemData", description="Client-supplied item data entries",
    )
    created_by: Optional[int] = Field(None, alias="createdBy", description="User ID that created the record")
    created_date: Optional[datetime] = Field(None, alias="createdDate", description="Creation date-time")
    modified_by: Optional[int] = Field(None, alias="modifiedBy", description="User ID that last modified the record")
    modified_date: Optional[datetime] = Field(None, alias="modifiedDate", description="Last modification date-time")


class AddLotRequest(RequestModel):
    """Body for ``POST /Lot``.

    All fields are optional per swagger — the server will reject an
    empty body with a 400 on its own side; the SDK does not duplicate
    that validation because swagger does not declare required fields.
    Callers typically supply at minimum ``platforms`` (for the lot's
    external identity), ``catalogs``, and ``initial_data``.
    """

    image_links: Optional[List[str]] = Field(
        None, alias="imageLinks", description="Image URLs attached to the lot",
    )
    item_data: Optional[List[LotDataDto]] = Field(
        None, alias="itemData", description="Item data entries (formerly ``overridenData``)",
    )
    catalogs: Optional[List[LotCatalogDto]] = Field(
        None, description="Catalogs this lot belongs to",
    )
    platforms: Optional[List[LotPlatformDto]] = Field(
        None, description="Platforms this lot is published to, with its external ID on each",
    )
    initial_data: Optional[LotDataDto] = Field(None, alias="initialData", description="Initial lot measurements")


class UpdateLotRequest(RequestModel):
    """Body for ``PUT /Lot/{id}``. Note: no ``initialData`` — updates
    cannot change the initial measurements."""

    image_links: Optional[List[str]] = Field(
        None, alias="imageLinks", description="Image URLs attached to the lot",
    )
    item_data: Optional[List[LotDataDto]] = Field(
        None, alias="itemData", description="Item data entries (formerly ``overridenData``)",
    )
    catalogs: Optional[List[LotCatalogDto]] = Field(
        None, description="Catalogs this lot belongs to",
    )
    platforms: Optional[List[LotPlatformDto]] = Field(
        None, description="Platforms this lot is published to, with its external ID on each",
    )


class AddLotClientItemDataRequest(RequestModel):
    """Body for ``POST /Lot/{id}/ClientItemData``."""

    client_item_data: Optional[List[LotDataDto]] = Field(
        None, alias="clientItemData", description="Client-supplied item data entries",
    )


class GetLotsItemDataQuery(RequestModel):
    """Body for ``POST /Lot/ItemData``.

    Despite the ``POST`` verb this is a read — the query is sent as a
    body because ``customer_item_ids`` can be long. ``partner_id`` is
    required per swagger and scopes the lookup to that partner's
    platforms.
    """

    partner_id: int = Field(..., alias="partnerId", description="Partner ID scoping the lookup")
    customer_comments: Optional[str] = Field(
        None, alias="customerComments", description="Filter by customer comments",
    )
    other_ref_no: Optional[str] = Field(None, alias="otherRefNo", description="Filter by other reference number")
    customer_item_ids: Optional[List[str]] = Field(
        None, alias="customerItemIds", description="Customer item IDs to look up",
    )


class LotListParams(RequestModel):
    """Query parameters for ``GET /Lot``."""

    id: Optional[int] = Field(None, alias="Id", description="Filter by lot ID")
    lot_number: Optional[str] = Field(None, alias="LotNumber", description="Filter by lot number")
    platform_item_id: Optional[str] = Field(
        None, alias="PlatformItemId", description="Filter by the lot's external ID on a platform",
    )
    page_size: Optional[int] = Field(None, alias="PageSize", description="Number of items per page")
    page_number: Optional[int] = Field(None, alias="PageNumber", description="Page number")


class LotClientItemDataListParams(RequestModel):
    """Query parameters for ``GET /Lot/{id}/ClientItemData``."""

    page_size: Optional[int] = Field(None, alias="PageSize", description="Number of items per page")
    page_number: Optional[int] = Field(None, alias="PageNumber", description="Page number")
