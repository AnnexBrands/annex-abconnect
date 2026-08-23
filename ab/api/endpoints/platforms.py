"""Platforms API endpoints (5 routes)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ab.api.models.platforms import AddPlatformRequest, PlatformDto, UpdatePlatformRequest
    from ab.api.models.shared import PaginatedList

from ab.api.base import BaseEndpoint
from ab.api.route import Route

_CREATE = Route(
    "POST", "/Platform",
    request_model="AddPlatformRequest", response_model="PlatformDto", api_surface="catalog",
)
_LIST = Route(
    "GET", "/Platform",
    params_model="PlatformListParams", response_model="PaginatedList[PlatformDto]", api_surface="catalog",
)
_GET = Route("GET", "/Platform/{id}", response_model="PlatformDto", api_surface="catalog")
_UPDATE = Route(
    "PUT", "/Platform/{id}",
    request_model="UpdatePlatformRequest", response_model="PlatformDto", api_surface="catalog",
)
_DELETE = Route("DELETE", "/Platform/{id}", api_surface="catalog")


class PlatformsEndpoint(BaseEndpoint):
    """Operations on platforms (Catalog API).

    Platforms are the external marketplaces a catalog or lot is published
    to. A platform ID plus an external ID is what replaced the retired
    ``customerCatalogId`` / ``customerItemId`` columns — see
    :mod:`ab.api.models.platforms`.
    """

    def create(self, *, data: AddPlatformRequest | dict) -> PlatformDto:
        """POST /Platform.

        Args:
            data: Platform creation payload with ``name``, ``partner_id``
                (required) and ``is_active`` (required). Accepts an
                :class:`AddPlatformRequest` instance or a dict.

        Request model: :class:`AddPlatformRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/platforms/create.html
        Request model: AddPlatformRequest
        Response model: PlatformDto
        """
        return self._request(_CREATE, json=data)

    def list(
        self,
        *,
        id: int | None = None,
        name: str | None = None,
        partner_id: int | None = None,
        is_active: bool | None = None,
        page_size: int = 25,
        page_number: int = 1,
    ) -> PaginatedList[PlatformDto]:
        """List platforms with optional filters.

        Args:
            id: Filter by platform ID.
            name: Filter by platform name.
            partner_id: Filter by owning partner ID.
            is_active: Filter by active status.
            page_size: Number of items per page.
            page_number: Page number (1-based).

        Returns:
            PaginatedList[PlatformDto]: Paginated platform results.
        """
        params = {
            "id": id,
            "name": name,
            "partner_id": partner_id,
            "is_active": is_active,
            "page_size": page_size,
            "page_number": page_number,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._paginated_request(_LIST, "PlatformDto", params=params)

    def get(self, platform_id: int) -> PlatformDto:
        """Retrieve a single platform by ID.

        Args:
            platform_id: Platform identifier.

        Returns:
            PlatformDto: Platform details.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/platforms/get.html
        Response model: PlatformDto
        """
        return self._request(_GET.bind(id=platform_id))

    def update(self, platform_id: int, *, data: UpdatePlatformRequest | dict) -> PlatformDto:
        """PUT /Platform/{id}.

        Args:
            platform_id: Platform identifier.
            data: Platform update payload — same shape as
                :class:`AddPlatformRequest`. Accepts an
                :class:`UpdatePlatformRequest` instance or a dict.

        Request model: :class:`UpdatePlatformRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/platforms/update.html
        Request model: UpdatePlatformRequest
        Response model: PlatformDto
        """
        return self._request(_UPDATE.bind(id=platform_id), json=data)

    def delete(self, platform_id: int) -> None:
        """Delete a platform.

        Args:
            platform_id: Platform identifier.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/platforms/delete.html
        """
        self._request(_DELETE.bind(id=platform_id))
