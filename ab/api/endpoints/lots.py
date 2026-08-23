"""Lots API endpoints (10 routes)."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ab.api.models.lots import (
        AddLotClientItemDataRequest,
        AddLotRequest,
        GetLotsItemDataQuery,
        LotClientItemDataDto,
        LotDto,
        LotItemDataDto,
        UpdateLotRequest,
    )
    from ab.api.models.shared import PaginatedList

from ab.api.base import BaseEndpoint
from ab.api.route import Route

_CREATE = Route("POST", "/Lot", request_model="AddLotRequest", response_model="LotDto", api_surface="catalog")
_LIST = Route(
    "GET", "/Lot",
    params_model="LotListParams", response_model="PaginatedList[LotDto]", api_surface="catalog",
)
_GET = Route("GET", "/Lot/{id}", response_model="LotDto", api_surface="catalog")
_UPDATE = Route("PUT", "/Lot/{id}", request_model="UpdateLotRequest", response_model="LotDto", api_surface="catalog")
_DELETE = Route("DELETE", "/Lot/{id}", api_surface="catalog")
_MERGE = Route("POST", "/Lot/{targetId}/merge/{sourceId}", response_model="LotDto", api_surface="catalog")
_ITEM_DATA = Route(
    "POST", "/Lot/ItemData",
    request_model="GetLotsItemDataQuery", response_model="List[LotItemDataDto]", api_surface="catalog",
)
_CLIENT_ITEM_DATA_CREATE = Route(
    "POST", "/Lot/{id}/ClientItemData",
    request_model="AddLotClientItemDataRequest", response_model="LotClientItemDataDto", api_surface="catalog",
)
_CLIENT_ITEM_DATA_LIST = Route(
    "GET", "/Lot/{id}/ClientItemData",
    params_model="LotClientItemDataListParams",
    response_model="PaginatedList[LotClientItemDataDto]", api_surface="catalog",
)
_CLIENT_ITEM_DATA_DELETE = Route(
    "DELETE", "/Lot/{lotId}/ClientItemData/{clientItemDataId}", api_surface="catalog",
)


class LotsEndpoint(BaseEndpoint):
    """Operations on lots (Catalog API)."""

    def create(self, *, data: AddLotRequest | dict) -> LotDto:
        """POST /Lot.

        Args:
            data: Lot creation payload with ``image_links``,
                ``initial_data`` (a :class:`LotDataDto` with the
                measurements), ``item_data``, ``catalogs`` (list of
                :class:`LotCatalogDto`), and ``platforms`` (list of
                :class:`LotPlatformDto` carrying the lot's external ID on
                each platform). Accepts an :class:`AddLotRequest`
                instance or a dict.

        Request model: :class:`AddLotRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/create.html
        Request model: AddLotRequest
        Response model: LotDto
        """
        return self._request(_CREATE, json=data)

    def list(
        self,
        *,
        id: int | None = None,
        lot_number: str | None = None,
        platform_item_id: str | None = None,
        page_size: int = 25,
        page_number: int = 1,
    ) -> PaginatedList[LotDto]:
        """List lots with optional filters.

        Args:
            id: Filter by lot ID.
            lot_number: Filter by lot number.
            platform_item_id: Filter by the lot's external ID on a platform.
            page_size: Number of items per page.
            page_number: Page number (1-based).

        Returns:
            PaginatedList[LotDto]: Paginated lot results.
        """
        params = {
            "id": id,
            "lot_number": lot_number,
            "platform_item_id": platform_item_id,
            "page_size": page_size,
            "page_number": page_number,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._paginated_request(_LIST, "LotDto", params=params)

    def get(self, lot_id: int) -> LotDto:
        """Retrieve a single lot by ID.

        Args:
            lot_id: Lot identifier.

        Returns:
            LotDto: Lot details.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/get.html
        Response model: LotDto
        """
        return self._request(_GET.bind(id=lot_id))

    def update(self, lot_id: int, *, data: UpdateLotRequest | dict) -> LotDto:
        """PUT /Lot/{id}.

        Args:
            lot_id: Lot identifier.
            data: Lot update payload with ``image_links``, ``item_data``,
                ``catalogs``, and ``platforms``. (``initial_data`` is
                create-only — it cannot be updated via PUT.) Accepts an
                :class:`UpdateLotRequest` instance or a dict.

        Request model: :class:`UpdateLotRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/update.html
        Request model: UpdateLotRequest
        Response model: LotDto
        """
        return self._request(_UPDATE.bind(id=lot_id), json=data)

    def delete(self, lot_id: int) -> None:
        """Delete a lot.

        Args:
            lot_id: Lot identifier.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/delete.html
        """
        self._request(_DELETE.bind(id=lot_id))

    def merge(self, target_id: int, source_id: int) -> LotDto:
        """POST /Lot/{targetId}/merge/{sourceId}.

        Folds the source lot's catalog and platform associations into the
        target lot and removes the source. Destructive — the source lot
        does not survive the call.

        Args:
            target_id: Lot that absorbs the associations and survives.
            source_id: Lot that is merged away.

        Returns:
            LotDto: The target lot after the merge.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/merge.html
        Response model: LotDto
        """
        return self._request(_MERGE.bind(targetId=target_id, sourceId=source_id))

    def item_data(self, *, data: GetLotsItemDataQuery | dict) -> List[LotItemDataDto]:
        """POST /Lot/ItemData.

        Looks up item data for lots by their customer item IDs. Despite
        the POST verb this is a read — the query travels in the body
        because the ID list can be long.

        Replaces the retired ``POST /Lot/get-overrides``.

        Args:
            data: Query payload with ``partner_id`` (required),
                ``customer_item_ids``, ``customer_comments`` and
                ``other_ref_no``. Accepts a :class:`GetLotsItemDataQuery`
                instance or a dict.

        Returns:
            list[LotItemDataDto]: Item data for the matched lots.

        Request model: :class:`GetLotsItemDataQuery`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/item_data.html
        Request model: GetLotsItemDataQuery
        Response model: List[LotItemDataDto]
        """
        return self._request(_ITEM_DATA, json=data)

    def create_client_item_data(
        self, lot_id: int, *, data: AddLotClientItemDataRequest | dict,
    ) -> LotClientItemDataDto:
        """POST /Lot/{id}/ClientItemData.

        Attaches a client-supplied item data record to a lot. Each call
        adds a new record — it does not replace the existing ones.

        Args:
            lot_id: Lot identifier.
            data: Payload with ``client_item_data`` (a list of
                :class:`LotDataDto`). Accepts an
                :class:`AddLotClientItemDataRequest` instance or a dict.

        Returns:
            LotClientItemDataDto: The created record with its audit fields.

        Request model: :class:`AddLotClientItemDataRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/create_client_item_data.html
        Request model: AddLotClientItemDataRequest
        Response model: LotClientItemDataDto
        """
        return self._request(_CLIENT_ITEM_DATA_CREATE.bind(id=lot_id), json=data)

    def list_client_item_data(
        self, lot_id: int, *, page_size: int = 25, page_number: int = 1,
    ) -> PaginatedList[LotClientItemDataDto]:
        """List the client item data records attached to a lot.

        Args:
            lot_id: Lot identifier.
            page_size: Number of items per page.
            page_number: Page number (1-based).

        Returns:
            PaginatedList[LotClientItemDataDto]: Paginated records.
        """
        params = {"page_size": page_size, "page_number": page_number}
        return self._paginated_request(
            _CLIENT_ITEM_DATA_LIST.bind(id=lot_id), "LotClientItemDataDto", params=params,
        )

    def delete_client_item_data(self, lot_id: int, client_item_data_id: int) -> None:
        """Delete one client item data record from a lot.

        Args:
            lot_id: Lot identifier.
            client_item_data_id: Client item data record identifier.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/lots/delete_client_item_data.html
        """
        self._request(
            _CLIENT_ITEM_DATA_DELETE.bind(lotId=lot_id, clientItemDataId=client_item_data_id),
        )
