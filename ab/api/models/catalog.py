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

    ``title``, ``start_date``, ``end_date``, ``is_completed`` and
    ``seller_id`` are required. Swagger declares ``title`` nullable; the API
    source requires it, so it is required here — a payload without one is a
    400 waiting to happen.

    ``agent_company_ids`` and ``platforms`` are collections, not tri-state
    flags: they default to an empty list rather than ``None``, so "no agent
    companies" and "no platforms" have exactly one representation.
    """

    agent_company_ids: List[str] = Field(
        default_factory=list, alias="agentCompanyIds", description="Agent company IDs to assign",
    )
    title: str = Field(..., description="Catalog title")
    start_date: datetime = Field(..., alias="startDate", description="Catalog start date-time")
    end_date: datetime = Field(..., alias="endDate", description="Catalog end date-time")
    is_completed: bool = Field(..., alias="isCompleted", description="Whether the catalog is completed")
    seller_id: int = Field(..., alias="sellerId", description="Owning seller ID")
    platforms: List[CatalogPlatformDto] = Field(
        default_factory=list,
        description="Platforms this catalog is published to, with its external ID on each",
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
    """Seller entry inside a bulk upsert payload.

    Every field is required. Swagger declares ``name`` nullable; the API
    source does not, and a bulk row has to name the seller it creates or
    matches.
    """

    name: str = Field(..., description="Seller name")
    customer_display_id: int = Field(..., alias="customerDisplayId", description="Customer display ID")
    is_active: bool = Field(..., alias="isActive", description="Whether the seller is active")


class BulkUpsertLotRequest(RequestModel):
    """Lot entry inside a bulk upsert payload.

    ``data`` is a single :class:`LotDataDto` — the bulk shape does not
    split initial and override measurements the way ``POST /Lot`` does.

    ``customer_item_id``, ``lot_number`` and ``data`` are required per the
    API source: the first two are the identity bulk matches rows on, and a
    lot with no ``data`` carries nothing to upsert. ``image_links`` is a
    collection and defaults to empty rather than ``None``.
    """

    customer_item_id: str = Field(..., alias="customerItemId", description="Customer item ID")
    lot_number: str = Field(..., alias="lotNumber", description="Lot number")
    image_links: List[str] = Field(
        default_factory=list, alias="imageLinks", description="Image URLs",
    )
    data: LotDataDto = Field(..., description="Lot measurements")


class BulkUpsertCatalogRequest(RequestModel):
    """Catalog entry inside a bulk upsert payload. Nests its lots and its
    single seller.

    ``customer_catalog_id``, ``title``, ``start_date``, ``end_date`` and
    ``seller`` are all required per the API source — swagger declares the
    first two nullable and gets both wrong, the same way it got ``seller``
    wrong (a payload without one answers ``400 Catalogs[0].Seller: The
    Seller field is required``; verified against staging on 2026-08-23).
    ``lots`` is a collection and defaults to empty rather than ``None``.

    ``platform_id`` does not appear in swagger at all: the property carries
    ``[SwaggerIgnore]``, which hides it from the generated document while
    leaving it a perfectly ordinary JSON property the API binds and reads.
    It is **required here for every caller**, which is stricter than the API:

    - **Corporate users** (``CorporateAdmin``, ``CorporateAccounting``) have
      no choice — their tokens intentionally carry no ``partnerIds`` claim,
      so the API has nothing to resolve a platform from and answers ``404``
      without one.
    - **Non-corporate users** *could* omit it: the API resolves their platform
      from ``partnerIds``. It is required here anyway so that one payload
      shape works for every caller and the intended platform is recorded in
      the body rather than left implicit in whoever held the token.

    Be aware of what the API does with the value, verified against staging on
    2026-08-28: for a non-corporate bearer it is **ignored**, not checked. A
    platform user on partner 1 who names platform 15 is silently given
    platform 11 — their own — with a ``200``, not an error. The value is
    authoritative only for corporate callers, who have no ``partnerIds`` to
    fall back to.

    A caller who does not know their platform ID can derive it from their own
    token: :meth:`~ab.http.HttpClient.bearer_claims` exposes ``partner_ids``,
    and ``api.platforms.list(partner_id=...)`` maps a partner to its
    platforms. Note what is *not* here: ``partnerIds`` is a claim on the
    token and never a property of the body.
    """

    customer_catalog_id: str = Field(..., alias="customerCatalogId", description="Customer catalog ID")
    title: str = Field(..., description="Catalog title")
    start_date: datetime = Field(..., alias="startDate", description="Catalog start date-time")
    end_date: datetime = Field(..., alias="endDate", description="Catalog end date-time")
    platform_id: int = Field(
        ...,
        alias="platformId",
        description=(
            "Platform this catalog belongs to. Required for every caller. "
            "Authoritative for corporate bearers, which carry no partnerIds "
            "for the API to resolve from; ignored for everyone else, whose "
            "platform the API takes from their partnerIds claim regardless."
        ),
    )
    lots: List[BulkUpsertLotRequest] = Field(
        default_factory=list, description="Lots in this catalog",
    )
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

    catalogs: List[BulkUpsertCatalogRequest] = Field(
        default_factory=list, description="Catalogs to upsert, each with nested lots and seller",
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
