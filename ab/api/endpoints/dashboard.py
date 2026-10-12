"""Dashboard API endpoints (9 routes)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ab.api.models.dashboard import DashboardCompanyRequest, DashboardGridParams
from ab.warnings import warn_legacy_request

if TYPE_CHECKING:
    from ab.api.models.dashboard import DashboardCompanyRequest, DashboardSummary, GridViewInfo, GridViewState

from ab.api.base import BaseEndpoint
from ab.api.route import Route

_GET = Route("GET", "/dashboard", params_model="DashboardParams", response_model="DashboardSummary")
_GET_GRID_VIEWS = Route(
    "GET", "/dashboard/gridviews", params_model="DashboardCompanyParams", response_model="List[GridViewInfo]"
)
_GET_GRID_VIEW_STATE = Route("GET", "/dashboard/gridviewstate/{id}", response_model="GridViewState")
_SAVE_GRID_VIEW_STATE = Route("POST", "/dashboard/gridviewstate/{id}", request_model="GridViewState")
_INBOUND = Route("POST", "/dashboard/inbound", request_model="DashboardGridOptions", params_model="DashboardGridParams")
_IN_HOUSE = Route(
    "POST", "/dashboard/inhouse", request_model="DashboardGridOptions", params_model="DashboardGridParams"
)
_OUTBOUND = Route(
    "POST", "/dashboard/outbound", request_model="DashboardGridOptions", params_model="DashboardGridParams"
)
_LOCAL_DELIVERIES = Route(
    "POST", "/dashboard/local-deliveries", request_model="DashboardGridOptions", params_model="DashboardGridParams"
)
_RECENT_ESTIMATES = Route(
    "POST", "/dashboard/recentestimates", request_model="DashboardGridOptions", params_model="DashboardGridParams"
)


class DashboardEndpoint(BaseEndpoint):
    """Dashboard operations (ACPortal API)."""

    def get(
        self,
        *,
        view_id: int | None = None,
        company_id: str | None = None,
    ) -> DashboardSummary:
        """Aggregated dashboard summary for one grid view.

        Both ``view_id`` and ``company_id`` are optional. When ``company_id``
        is omitted the API defaults to the active user's primary company —
        the call does not 4xx. ``view_id`` is the ``id`` of a row returned
        by :meth:`get_grid_views`.

        Args:
            view_id: Grid view id (forward reference: :class:`GridViewInfo.id`).
            company_id: Company UUID; defaults to the caller's primary company.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/get.html
        Query params: DashboardParams
        Response model: DashboardSummary
        """
        return self._request(_GET, params=dict(view_id=view_id, company_id=company_id))

    def get_grid_views(self) -> list[GridViewInfo]:
        """List the grid views available to the caller.

        Each row carries the ``id`` you pass to :meth:`get` as ``view_id``,
        plus ``name``, ``dataKey``, and ``isActive``.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/get_grid_views.html
        Query params: DashboardCompanyParams
        Response model: List[GridViewInfo]
        """
        return self._request(_GET_GRID_VIEWS)

    def get_grid_view_state(self, view_id: str) -> GridViewState:
        """Fetch the saved column / filter / sort state for a grid view.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/get_grid_view_state.html
        Response model: GridViewState
        """
        return self._request(_GET_GRID_VIEW_STATE.bind(id=view_id))

    def save_grid_view_state(self, view_id: str, *, data: GridViewState | dict) -> None:
        """POST /dashboard/gridviewstate/{id}.

        Args:
            view_id: View state identifier.
            data: Grid view state with columns, filters, and sort_order.
                Accepts a :class:`GridViewState` instance or a dict.

        Request model: :class:`GridViewState`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/save_grid_view_state.html
        Request model: GridViewState
        """
        return self._request(_SAVE_GRID_VIEW_STATE.bind(id=view_id), json=data)

    def inbound(
        self,
        *,
        company_id: str | None = None,
        data: DashboardCompanyRequest | dict | None = None,
        **options: Any,
    ) -> Any:
        """POST /dashboard/inbound.

        Args:
            company_id: Company UUID sent as a query parameter.
            data: Legacy company-only body, adapted to the query parameter with a warning.
            **options: Grid paging, filtering, and sorting options sent in the JSON body.

        Request model: :class:`DashboardCompanyRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/inbound.html
        Request model: DashboardGridOptions
        Query params: DashboardGridParams
        """
        params = self._company_params(company_id, data)
        return self._request(_INBOUND, params=params, json=options)

    def in_house(
        self,
        *,
        company_id: str | None = None,
        data: DashboardCompanyRequest | dict | None = None,
        **options: Any,
    ) -> Any:
        """POST /dashboard/inhouse.

        Args:
            company_id: Company UUID sent as a query parameter.
            data: Legacy company-only body, adapted to the query parameter with a warning.
            **options: Grid paging, filtering, and sorting options sent in the JSON body.

        Request model: :class:`DashboardCompanyRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/in_house.html
        Request model: DashboardGridOptions
        Query params: DashboardGridParams
        """
        params = self._company_params(company_id, data)
        return self._request(_IN_HOUSE, params=params, json=options)

    def outbound(
        self,
        *,
        company_id: str | None = None,
        data: DashboardCompanyRequest | dict | None = None,
        **options: Any,
    ) -> Any:
        """POST /dashboard/outbound.

        Args:
            company_id: Company UUID sent as a query parameter.
            data: Legacy company-only body, adapted to the query parameter with a warning.
            **options: Grid paging, filtering, and sorting options sent in the JSON body.

        Request model: :class:`DashboardCompanyRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/outbound.html
        Request model: DashboardGridOptions
        Query params: DashboardGridParams
        """
        params = self._company_params(company_id, data)
        return self._request(_OUTBOUND, params=params, json=options)

    def local_deliveries(
        self,
        *,
        company_id: str | None = None,
        data: DashboardCompanyRequest | dict | None = None,
        **options: Any,
    ) -> Any:
        """POST /dashboard/local-deliveries.

        Args:
            company_id: Company UUID sent as a query parameter.
            data: Legacy company-only body, adapted to the query parameter with a warning.
            **options: Grid paging, filtering, and sorting options sent in the JSON body.

        Request model: :class:`DashboardCompanyRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/local_deliveries.html
        Request model: DashboardGridOptions
        Query params: DashboardGridParams
        """
        params = self._company_params(company_id, data)
        return self._request(_LOCAL_DELIVERIES, params=params, json=options)

    def recent_estimates(
        self,
        *,
        company_id: str | None = None,
        data: DashboardCompanyRequest | dict | None = None,
        **options: Any,
    ) -> Any:
        """POST /dashboard/recentestimates.

        Args:
            company_id: Company UUID sent as a query parameter.
            data: Legacy company-only body, adapted to the query parameter with a warning.
            **options: Grid paging, filtering, and sorting options sent in the JSON body.

        Request model: :class:`DashboardCompanyRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/dashboard/recent_estimates.html
        Request model: DashboardGridOptions
        Query params: DashboardGridParams
        """
        params = self._company_params(company_id, data)
        return self._request(_RECENT_ESTIMATES, params=params, json=options)

    @staticmethod
    def _company_params(company_id: str | None, data: DashboardCompanyRequest | dict | None) -> dict:
        if data is not None:
            warn_legacy_request("dashboard feed data={companyId: ...}", "dashboard feed company_id=...")
            legacy = DashboardCompanyRequest.check(data).get("companyId")
            if company_id is not None and legacy is not None:
                if DashboardGridParams.check({"company_id": company_id}) != DashboardGridParams.check(
                    {"company_id": legacy}
                ):
                    raise ValueError("Conflicting company_id and legacy data.companyId")
            company_id = company_id if company_id is not None else legacy
        return DashboardGridParams.check({"company_id": company_id})
