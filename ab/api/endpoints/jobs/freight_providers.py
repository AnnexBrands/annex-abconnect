"""Job-scoped freight-provider operations — swagger tag ``JobFreightProviders``.

Exposed as ``api.jobs.freight_providers``. Old names on
:class:`~ab.api.endpoints.jobs.JobsEndpoint` remain as deprecation shims.

Method renames (``_freight_provider(s)`` suffix dropped):

* :meth:`list`           (was ``list_freight_providers``)
* :meth:`save`           (was ``save_freight_providers``)
* :meth:`rate_quote`     (was ``get_freight_provider_rate_quote``)

Note: ``add_freight_items`` is tagged ``Job`` in swagger, not
``JobFreightProviders``, so it remains on :class:`JobsEndpoint`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ab.api.models.jobs import (
        PricedFreightProvider,
        RateQuoteRequest,
        ShipmentPlanProvider,
    )
    from ab.api.models.shared import ServiceBaseResponse

from ab.api.base import BaseEndpoint
from ab.api.route import Route

_LIST = Route(
    "GET",
    "/job/{jobDisplayId}/freightproviders",
    params_model="FreightProvidersParams",
    response_model="List[PricedFreightProvider]",
)
_SAVE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders",
    request_model="ShipmentPlanProvider",
    response_model="ServiceBaseResponse",
)
_RATE_QUOTE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders/{optionIndex}/ratequote",
    request_model="RateQuoteRequest",
)


class JobFreightProvidersEndpoint(BaseEndpoint):
    """Job-scoped freight-provider operations (ACPortal API)."""

    def list(
        self,
        job_display_id: int,
        *,
        provider_indexes: list[int] | None = None,
        shipment_types: list[str] | None = None,
        only_active: bool | None = None,
    ) -> list[PricedFreightProvider]:
        """``GET /job/{jobDisplayId}/freightproviders``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.list.html
        Query params: FreightProvidersParams
        Response model: List[PricedFreightProvider]
        """
        return self._request(
            _LIST.bind(jobDisplayId=job_display_id),
            params=dict(
                provider_indexes=provider_indexes,
                shipment_types=shipment_types,
                only_active=only_active,
            ),
        )

    def save(
        self,
        job_display_id: int,
        *,
        data: ShipmentPlanProvider | dict | list[ShipmentPlanProvider | dict],
    ) -> ServiceBaseResponse | None:
        """``POST /job/{jobDisplayId}/freightproviders``

        Request model: :class:`ShipmentPlanProvider`. API 7.11 binds this
        route as ``List[ShipmentPlanProvider]``; a single row is accepted for
        compatibility and wrapped into a one-item array before dispatch.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.save.html
        Request model: ShipmentPlanProvider
        Response model: ServiceBaseResponse
        """
        rows = data if isinstance(data, list) else [data]
        return self._request(_SAVE.bind(jobDisplayId=job_display_id), json=rows)

    def final_override(
        self,
        job_display_id: int,
        *,
        provider: str | None = None,
        provider_id: str | None = None,
        provider_company_code: str | None = None,
        shipment_type: str | None = None,
        freight_amount: float | None = None,
        accessorial_amount: float | None = None,
        pro_num: str | None = None,
        option_index: int = 6,
        option_active: bool | None = None,
        data: ShipmentPlanProvider | dict | list[ShipmentPlanProvider | dict] | None = None,
    ) -> ServiceBaseResponse | None:
        """``POST /job/{jobDisplayId}/freightproviders``

        Saves a final freight-provider override on API 7.11 by posting a
        one-item :class:`ShipmentPlanProvider` array to the regular save route.
        When ``data`` is omitted, the SDK builds the minimal body from provider
        identifiers, shipment type, PRO number, and ``optionIndex=6``. The API
        requires ``optionIndex`` to be present, so it is added to every row when
        omitted.

        Request model: :class:`ShipmentPlanProvider`.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.final_override.html
        Request model: ShipmentPlanProvider
        Response model: ServiceBaseResponse
        """
        if data is None:
            rows: list[ShipmentPlanProvider | dict] = [
                {
                    "providerCompanyName": provider,
                    "providerID": provider_id,
                    "providerCompanyCode": provider_company_code,
                    "shipmentType": shipment_type,
                    "freightAmount": freight_amount,
                    "accessorialAmount": accessorial_amount,
                    "proNum": pro_num,
                    "optionIndex": option_index,
                    "optionActive": option_active,
                }
            ]
        elif isinstance(data, list):
            rows = data
        else:
            rows = [data]

        payload = []
        for row in rows:
            item = (
                row.model_dump(by_alias=True, exclude_none=True, mode="json")
                if hasattr(row, "model_dump")
                else dict(row)
            )
            item = {key: value for key, value in item.items() if value is not None}
            item.setdefault("optionIndex", option_index)
            payload.append(item)

        return self._request(_SAVE.bind(jobDisplayId=job_display_id), json=payload)

    def rate_quote(
        self,
        job_display_id: int,
        option_index: int,
        *,
        data: RateQuoteRequest | dict,
    ) -> None:
        """``POST /job/{jobDisplayId}/freightproviders/{optionIndex}/ratequote``

        Request model: :class:`RateQuoteRequest`.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.rate_quote.html
        Request model: RateQuoteRequest
        """
        return self._request(
            _RATE_QUOTE.bind(jobDisplayId=job_display_id, optionIndex=option_index),
            json=data,
        )
