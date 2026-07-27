"""Commodity models for the ACPortal API."""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel
from ab.api.models.mixins import SearchableRequestMixin


class Commodity(ResponseModel):
    """Commodity record — GET /commodity/{id}."""

    # Integer primary key. Live: {"id": 1, ...} from POST /commodity/search.
    id: Optional[int] = Field(None, description="Commodity ID")
    code: Optional[str] = Field(None, description="Commodity code")
    name: Optional[str] = Field(None, description="Commodity name")
    description: Optional[str] = Field(None, description="Commodity description")
    is_active: Optional[bool] = Field(None, alias="isActive", description="Whether the commodity is active")
    # Commodities form a tree: search returns each row with its parent denormalized.
    parent_id: Optional[int] = Field(None, alias="parentId", description="Parent commodity ID")
    parent_name: Optional[str] = Field(None, alias="parentName", description="Parent commodity name")
    parent_code: Optional[str] = Field(None, alias="parentCode", description="Parent commodity code")
    parent_is_active: Optional[bool] = Field(
        None, alias="parentIsActive", description="Whether the parent commodity is active",
    )
    # Freight attributes — returned by GET /commodity/{id}, absent from search rows.
    freight_class: Optional[str] = Field(None, alias="freightClass", description="Freight class")
    nmfc_code: Optional[str] = Field(None, alias="nmfcCode", description="NMFC code")
    weight_min: Optional[float] = Field(None, alias="weightMin", description="Minimum weight")
    weight_max: Optional[float] = Field(None, alias="weightMax", description="Maximum weight")


class CommodityCreateRequest(RequestModel):
    """Body for POST /commodity."""

    description: Optional[str] = Field(None, description="Commodity description")
    freight_class: Optional[str] = Field(None, alias="freightClass", description="Freight class")
    nmfc_code: Optional[str] = Field(None, alias="nmfcCode", description="NMFC code")
    weight_min: Optional[float] = Field(None, alias="weightMin", description="Minimum weight")
    weight_max: Optional[float] = Field(None, alias="weightMax", description="Maximum weight")


class CommodityUpdateRequest(RequestModel):
    """Body for PUT /commodity/{id}."""

    description: Optional[str] = Field(None, description="Commodity description")
    freight_class: Optional[str] = Field(None, alias="freightClass", description="Freight class")
    nmfc_code: Optional[str] = Field(None, alias="nmfcCode", description="NMFC code")


class CommoditySearchRequest(SearchableRequestMixin):
    """Search filter for POST /commodity/search."""

    page: Optional[int] = Field(None, description="Page number")
    page_size: Optional[int] = Field(None, alias="pageSize", description="Results per page")


class CommoditySuggestionRequest(SearchableRequestMixin):
    """Suggestion filter for POST /commodity/suggestions."""


class CommodityMap(ResponseModel):
    """Commodity mapping record — GET /commodity-map/{id}."""

    id: Optional[str] = Field(None, description="Map ID")
    custom_name: Optional[str] = Field(None, alias="customName", description="Custom commodity name")
    commodity_id: Optional[str] = Field(None, alias="commodityId", description="Linked commodity ID")


class CommodityMapCreateRequest(RequestModel):
    """Body for POST /commodity-map."""

    custom_name: Optional[str] = Field(None, alias="customName", description="Custom commodity name")
    commodity_id: Optional[str] = Field(None, alias="commodityId", description="Linked commodity ID")


class CommodityMapUpdateRequest(RequestModel):
    """Body for PUT /commodity-map/{id}."""

    custom_name: Optional[str] = Field(None, alias="customName", description="Custom commodity name")
    commodity_id: Optional[str] = Field(None, alias="commodityId", description="Linked commodity ID")


class CommodityMapSearchRequest(SearchableRequestMixin):
    """Search filter for POST /commodity-map/search."""

    page: Optional[int] = Field(None, description="Page number")
    page_size: Optional[int] = Field(None, alias="pageSize", description="Results per page")
