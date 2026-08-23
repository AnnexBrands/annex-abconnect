"""Catalog API models.

Field shapes ported against ``ab/api/schemas/catalog.json`` (swagger,
Tier 3) with ``ABConnectTools/ABConnect/api/models/catalog.py`` as
secondary reference (Tier 4). The prior placeholder implementation
had invented field names for ``AddCatalogRequest``,
``UpdateCatalogRequest``, and ``BulkInsertRequest`` that did not match
either source — see ``specs/036-lotsdb-migration-prep/gap-recommendations.md``.

**Staging schema migration.** These models target the migrated Catalog
schema, which at the time of writing is deployed to staging only. The
breaking changes all follow the database's retired columns:

- ``Catalogs.Agent`` is retired (``ObsoleteAgent``). Agents are now a
  many-to-many through ``CatalogAgentCompanies``, surfaced as
  ``agentCompanyIds``.
- ``Catalogs.CustomerCatalogId`` is retired
  (``ObsoleteCustomerCatalogId``). The catalog's external identity now
  lives per-platform on
  :class:`~ab.api.models.platforms.CatalogPlatformDto.platform_catalog_id`.
- A catalog now has **one** seller (``Catalogs.SellerId``), not a list.
  ``CatalogWithSellersDto`` is gone; reads return ``seller`` and writes
  take ``sellerId``.

The bulk upsert models are the exception — they still speak
``customerCatalogId`` / ``customerItemId`` because bulk import matches
incoming rows on the caller's own identifiers.

``SellerDto`` is a TYPE_CHECKING-only import to break the
``catalog`` ↔ ``sellers`` circular reference; :func:`_rebuild_catalog_models`
at the bottom of the module does the runtime import and calls
``model_rebuild()`` on any class whose annotations need it.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel
from ab.api.models.lots import LotCatalogInformationDto, LotDataDto
from ab.api.models.platforms import CatalogPlatformDto

if TYPE_CHECKING:
    from ab.api.models.sellers import SellerDto


class CatalogDto(ResponseModel):
    """Core catalog information — parent of :class:`CatalogExpandedDto`
    and embedded in ``SellerExpandedDto.catalogs``."""

    id: int = Field(..., description="Catalog ID")
    agent_company_ids: Optional[List[str]] = Field(
        None, alias="agentCompanyIds", description="Agent company IDs assigned to the catalog",
    )
    title: Optional[str] = Field(None, description="Catalog title")
    start_date: datetime = Field(..., alias="startDate", description="Catalog start date-time")
    end_date: datetime = Field(..., alias="endDate", description="Catalog end date-time")
    is_completed: bool = Field(..., alias="isCompleted", description="Whether the catalog is completed")


class CatalogExpandedDto(CatalogDto):
    """Catalog with its seller and platform associations — returned by
    ``POST /Catalog`` and ``PUT /Catalog/{id}``."""

    seller: Optional["SellerDto"] = Field(None, description="Owning seller")
    platforms: Optional[List[CatalogPlatformDto]] = Field(
        None, description="Platform associations carrying the catalog's external IDs",
    )


class CatalogWithLotsDto(CatalogExpandedDto):
    """Catalog with seller, platforms and lot summaries — returned by
    ``GET /Catalog``, ``GET /Catalog/{id}``,
    ``POST /Catalog/{targetId}/merge/{sourceId}`` and
    ``POST /Bulk/upsert``."""

    lots: Optional[List[LotCatalogInformationDto]] = Field(
        None, description="Lot summaries belonging to the catalog",
    )


class AddCatalogRequest(RequestModel):
    """Body for ``POST /Catalog``.

    ``start_date``, ``end_date``, ``is_completed`` and ``seller_id`` are
    required per swagger (no ``nullable: true``). All other fields are
    optional.
    """

    agent_company_ids: Optional[List[str]] = Field(
        None, alias="agentCompanyIds", description="Agent company IDs to assign",
    )
    title: Optional[str] = Field(None, description="Catalog title")
    start_date: datetime = Field(..., alias="startDate", description="Catalog start date-time")
    end_date: datetime = Field(..., alias="endDate", description="Catalog end date-time")
    is_completed: bool = Field(..., alias="isCompleted", description="Whether the catalog is completed")
    seller_id: int = Field(..., alias="sellerId", description="Owning seller ID")
    platforms: Optional[List[CatalogPlatformDto]] = Field(
        None, description="Platforms this catalog is published to, with its external ID on each",
    )


class UpdateCatalogRequest(AddCatalogRequest):
    """Body for ``PUT /Catalog/{id}``. Same shape as :class:`AddCatalogRequest`
    per swagger."""


class CatalogListParams(RequestModel):
    """Query parameters for ``GET /Catalog``."""

    id: Optional[int] = Field(None, alias="Id", description="Filter by catalog ID")
    agent_company_id: Optional[str] = Field(
        None, alias="AgentCompanyId", description="Filter by assigned agent company ID",
    )
    platform_catalog_id: Optional[str] = Field(
        None, alias="PlatformCatalogId", description="Filter by the catalog's external ID on a platform",
    )
    title: Optional[str] = Field(None, alias="Title", description="Filter by title")
    start_date: Optional[str] = Field(None, alias="StartDate", description="Filter by start date (date-time)")
    end_date: Optional[str] = Field(None, alias="EndDate", description="Filter by end date (date-time)")
    is_completed: Optional[bool] = Field(None, alias="IsCompleted", description="Filter by completion status")
    seller_ids: Optional[List[int]] = Field(None, alias="SellerIds", description="Filter by seller IDs")
    page_size: Optional[int] = Field(None, alias="PageSize", description="Number of items per page")
    page_number: Optional[int] = Field(None, alias="PageNumber", description="Page number")


# =============================================================================
# Bulk request models
# =============================================================================


class BulkUpsertSellerRequest(RequestModel):
    """Seller entry inside a bulk upsert payload."""

    name: Optional[str] = Field(None, description="Seller name")
    customer_display_id: int = Field(..., alias="customerDisplayId", description="Customer display ID")
    is_active: bool = Field(..., alias="isActive", description="Whether the seller is active")


class BulkUpsertLotRequest(RequestModel):
    """Lot entry inside a bulk upsert payload.

    ``data`` is a single :class:`LotDataDto` — the bulk shape does not
    split initial and override measurements the way ``POST /Lot`` does.
    """

    customer_item_id: Optional[str] = Field(None, alias="customerItemId", description="Customer item ID")
    lot_number: Optional[str] = Field(None, alias="lotNumber", description="Lot number")
    image_links: Optional[List[str]] = Field(None, alias="imageLinks", description="Image URLs")
    data: Optional[LotDataDto] = Field(None, description="Lot measurements")


class BulkUpsertCatalogRequest(RequestModel):
    """Catalog entry inside a bulk upsert payload. Nests its lots and its
    single seller.

    ``seller`` is **required**, which swagger gets wrong — it declares the
    property nullable, but the API answers a payload without it with
    ``400 Catalogs[0].Seller: The Seller field is required``. Verified
    against staging on 2026-08-23.
    """

    customer_catalog_id: Optional[str] = Field(None, alias="customerCatalogId", description="Customer catalog ID")
    title: Optional[str] = Field(None, description="Catalog title")
    start_date: datetime = Field(..., alias="startDate", description="Catalog start date-time")
    end_date: datetime = Field(..., alias="endDate", description="Catalog end date-time")
    lots: Optional[List[BulkUpsertLotRequest]] = Field(None, description="Lots in this catalog")
    seller: BulkUpsertSellerRequest = Field(..., description="Seller that owns this catalog")


class BulkUpsertRequest(RequestModel):
    """Body for ``POST /Bulk/upsert``.

    Per swagger, the top-level payload contains exactly one key —
    ``catalogs`` — a list of :class:`BulkUpsertCatalogRequest`. Each
    nested catalog carries its own lots and seller. This is a nested
    bulk shape, *not* a flat list of rows.

    Rows are matched on ``customer_catalog_id`` / ``customer_item_id``,
    so re-sending a payload updates the existing records rather than
    duplicating them — the behaviour change from the retired
    ``POST /Bulk/insert``.
    """

    catalogs: Optional[List[BulkUpsertCatalogRequest]] = Field(
        None, description="Catalogs to upsert, each with nested lots and seller",
    )


def _rebuild_catalog_models() -> None:
    """Resolve the TYPE_CHECKING forward reference to ``SellerDto``.

    Deferred because ``sellers.py`` imports :class:`CatalogDto` from
    this module — a real import of ``SellerDto`` at the top of this
    file would create a load-time cycle.
    """
    from ab.api.models.sellers import SellerDto  # noqa: F401

    CatalogExpandedDto.model_rebuild()
    CatalogWithLotsDto.model_rebuild()


_rebuild_catalog_models()
