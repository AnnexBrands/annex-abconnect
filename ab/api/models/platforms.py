"""Platform models for the Catalog API.

New surface introduced by the staging Catalog schema migration. Platforms
are the external marketplaces/partners a catalog or lot is published to;
the ``Platforms`` table joins to catalogs through ``PlatformCatalogs`` and
to lots through ``PlatformLots``.

The two association DTOs live here rather than in ``catalog.py`` /
``lots.py`` because both of those modules import them and this module
imports neither — keeping the platform models dependency-free avoids
another circular-import dance like the ``catalog`` ↔ ``sellers`` one.

The join rows carry the external identity that used to live directly on
the parent row: ``PlatformCatalogs.PlatformCatalogId`` replaces the
retired ``Catalogs.CustomerCatalogId``, and ``PlatformLots.PlatformItemId``
replaces the retired ``Lots.CustomerItemId``. A catalog or lot can now
carry a different external ID per platform, which the single obsolete
column could not express.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel


class PlatformDto(ResponseModel):
    """A platform — returned by every ``/Platform`` route."""

    id: int = Field(..., description="Platform ID")
    name: Optional[str] = Field(None, description="Platform name")
    partner_id: int = Field(..., alias="partnerId", description="Owning partner ID")
    is_active: bool = Field(..., alias="isActive", description="Whether the platform is active")


class CatalogPlatformDto(ResponseModel):
    """Catalog-to-platform association. Also used as a body fragment in
    :class:`~ab.api.models.catalog.AddCatalogRequest` and
    :class:`~ab.api.models.catalog.UpdateCatalogRequest`.

    ``platform_catalog_id`` is the catalog's external ID *on that
    platform* — the replacement for the retired top-level
    ``customerCatalogId``. It is **required**: the association exists to
    carry that ID, so supplying a platform entry without one associates a
    catalog to a platform under no external identity at all.
    """

    platform_id: int = Field(..., alias="platformId", description="Platform ID")
    platform_catalog_id: str = Field(
        ..., alias="platformCatalogId", description="Catalog's external ID on this platform",
    )


class LotPlatformDto(ResponseModel):
    """Lot-to-platform association. Also used as a body fragment in
    :class:`~ab.api.models.lots.AddLotRequest` and
    :class:`~ab.api.models.lots.UpdateLotRequest`.

    ``platform_item_id`` is the lot's external ID *on that platform* — the
    replacement for the retired top-level ``customerItemId``.
    """

    platform_id: int = Field(..., alias="platformId", description="Platform ID")
    platform_item_id: Optional[str] = Field(
        None, alias="platformItemId", description="Lot's external ID on this platform",
    )


class AddPlatformRequest(RequestModel):
    """Body for ``POST /Platform``."""

    name: Optional[str] = Field(None, description="Platform name")
    partner_id: int = Field(..., alias="partnerId", description="Owning partner ID")
    is_active: bool = Field(..., alias="isActive", description="Whether the platform is active")


class UpdatePlatformRequest(AddPlatformRequest):
    """Body for ``PUT /Platform/{id}``. Same shape as
    :class:`AddPlatformRequest` per swagger."""


class PlatformListParams(RequestModel):
    """Query parameters for ``GET /Platform``."""

    id: Optional[int] = Field(None, alias="Id", description="Filter by platform ID")
    name: Optional[str] = Field(None, alias="Name", description="Filter by platform name")
    partner_id: Optional[int] = Field(None, alias="PartnerId", description="Filter by partner ID")
    is_active: Optional[bool] = Field(None, alias="IsActive", description="Filter by active status")
    page_size: Optional[int] = Field(None, alias="PageSize", description="Number of items per page")
    page_number: Optional[int] = Field(None, alias="PageNumber", description="Page number")
