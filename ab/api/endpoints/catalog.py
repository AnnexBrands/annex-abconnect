"""Catalog API endpoints (7 routes)."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ab.api.models.catalog import (
        AddCatalogRequest,
        BulkUpsertRequest,
        CatalogExpandedDto,
        CatalogWithLotsDto,
        UpdateCatalogRequest,
    )
    from ab.api.models.shared import PaginatedList

from ab.api.base import BaseEndpoint
from ab.api.route import Route

# Routes — Catalog API surface
_CREATE = Route(
    "POST", "/Catalog",
    request_model="AddCatalogRequest", response_model="CatalogExpandedDto", api_surface="catalog",
)
_LIST = Route(
    "GET", "/Catalog",
    params_model="CatalogListParams", response_model="PaginatedList[CatalogWithLotsDto]", api_surface="catalog",
)
_GET = Route("GET", "/Catalog/{id}", response_model="CatalogWithLotsDto", api_surface="catalog")
_UPDATE = Route(
    "PUT", "/Catalog/{id}",
    request_model="UpdateCatalogRequest", response_model="CatalogExpandedDto", api_surface="catalog",
)
_DELETE = Route("DELETE", "/Catalog/{id}", api_surface="catalog")
_MERGE = Route(
    "POST", "/Catalog/{targetId}/merge/{sourceId}",
    response_model="CatalogWithLotsDto", api_surface="catalog",
)
_BULK_UPSERT = Route(
    "POST", "/Bulk/upsert",
    request_model="BulkUpsertRequest", response_model="List[CatalogWithLotsDto]", api_surface="catalog",
)


class CatalogEndpoint(BaseEndpoint):
    """Operations on catalogs (Catalog API)."""

    def create(self, *, data: AddCatalogRequest | dict) -> CatalogExpandedDto:
        """POST /Catalog.

        Args:
            data: Catalog creation payload with ``title``, ``start_date``
                and ``end_date`` (required datetimes), ``is_completed``,
                ``seller_id`` (required — a catalog belongs to exactly one
                seller), ``agent_company_ids``, and ``platforms``.
                Accepts an :class:`AddCatalogRequest` instance or a dict.

        Request model: :class:`AddCatalogRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/create.html
        Request model: AddCatalogRequest
        Response model: CatalogExpandedDto
        """
        return self._request(_CREATE, json=data)

    def list(
        self,
        *,
        id: int | None = None,
        agent_company_id: str | None = None,
        platform_catalog_id: str | None = None,
        title: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        is_completed: bool | None = None,
        seller_ids: list[int] | None = None,
        page_size: int = 25,
        page_number: int = 1,
    ) -> PaginatedList[CatalogWithLotsDto]:
        """List catalogs with optional filters.

        Args:
            id: Filter by catalog ID.
            agent_company_id: Filter by assigned agent company ID.
            platform_catalog_id: Filter by the catalog's external ID on a platform.
            title: Filter by catalog title.
            start_date: Filter by start date (ISO 8601 date-time string).
            end_date: Filter by end date (ISO 8601 date-time string).
            is_completed: Filter by completion status.
            seller_ids: Filter by seller IDs.
            page_size: Number of items per page.
            page_number: Page number (1-based).

        Returns:
            PaginatedList[CatalogWithLotsDto]: Paginated catalog results.
        """
        params = {
            "id": id,
            "agent_company_id": agent_company_id,
            "platform_catalog_id": platform_catalog_id,
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "is_completed": is_completed,
            "seller_ids": seller_ids,
            "page_size": page_size,
            "page_number": page_number,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._paginated_request(_LIST, "CatalogWithLotsDto", params=params)

    def get(self, catalog_id: int) -> CatalogWithLotsDto:
        """Retrieve a single catalog by ID.

        Args:
            catalog_id: Catalog identifier.

        Returns:
            CatalogWithLotsDto: Catalog details with seller, platforms and lots.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/get.html
        Response model: CatalogWithLotsDto
        """
        return self._request(_GET.bind(id=catalog_id))

    def update(self, catalog_id: int, *, data: UpdateCatalogRequest | dict) -> CatalogExpandedDto:
        """PUT /Catalog/{id}.

        Args:
            catalog_id: Catalog identifier.
            data: Catalog update payload — same shape as
                :class:`AddCatalogRequest`, including required
                ``start_date``, ``end_date``, ``is_completed`` and
                ``seller_id``. Accepts an :class:`UpdateCatalogRequest`
                instance or a dict.

        Request model: :class:`UpdateCatalogRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/update.html
        Request model: UpdateCatalogRequest
        Response model: CatalogExpandedDto
        """
        return self._request(_UPDATE.bind(id=catalog_id), json=data)

    def delete(self, catalog_id: int) -> None:
        """Delete a catalog.

        Args:
            catalog_id: Catalog identifier.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/delete.html
        """
        self._request(_DELETE.bind(id=catalog_id))

    def merge(self, target_id: int, source_id: int) -> CatalogWithLotsDto:
        """POST /Catalog/{targetId}/merge/{sourceId}.

        Folds the source catalog's lots into the target catalog and
        removes the source. Destructive — the source catalog does not
        survive the call.

        Args:
            target_id: Catalog that absorbs the lots and survives.
            source_id: Catalog that is merged away.

        Returns:
            CatalogWithLotsDto: The target catalog after the merge.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/merge.html
        Response model: CatalogWithLotsDto
        """
        return self._request(_MERGE.bind(targetId=target_id, sourceId=source_id))

    def bulk_upsert(self, *, data: BulkUpsertRequest | dict) -> List[CatalogWithLotsDto]:
        """POST /Bulk/upsert.

        Args:
            data: Bulk upsert payload — a :class:`BulkUpsertRequest`
                with a single ``catalogs`` list. Each entry is a
                :class:`BulkUpsertCatalogRequest` containing nested
                ``lots`` (:class:`BulkUpsertLotRequest`) and a single
                ``seller`` (:class:`BulkUpsertSellerRequest`). The
                top-level shape is a nested tree, *not* a flat list.
                Accepts a :class:`BulkUpsertRequest` instance or a dict.

                Rows are matched on ``customer_catalog_id`` /
                ``customer_item_id``, so re-sending a payload updates the
                existing records instead of duplicating them.

        Returns:
            list[CatalogWithLotsDto]: The upserted catalogs.

        Request model: :class:`BulkUpsertRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/catalog/bulk_upsert.html
        Request model: BulkUpsertRequest
        Response model: List[CatalogWithLotsDto]
        """
        return self._request(_BULK_UPSERT, json=data)
