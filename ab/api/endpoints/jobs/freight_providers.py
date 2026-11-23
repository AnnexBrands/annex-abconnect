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

from datetime import datetime
from typing import TYPE_CHECKING, Literal, NamedTuple
from uuid import UUID, uuid4

from ab.api.base import BaseEndpoint
from ab.api.models.release_support import (
    CreateOverriddenQuoteResponseResult,
    FinalOverrideRequest,
    JobModifiedDateServiceResponseResult,
    SaveFinalQuoteRequest,
    SaveRateQuoteResponseResult,
    SelectRateQuoteRequest,
    TransportationQuoteResult,
)
from ab.api.route import Route

if TYPE_CHECKING:
    from ab.api.models.jobs import (
        PricedFreightProvider,
        RateQuoteRequest,
        ShipmentPlanProvider,
    )
    from ab.api.models.shared import ServiceBaseResponse


class NewFinalOverride(NamedTuple):
    """Result of :meth:`JobFreightProvidersEndpoint.save_new_final_override`."""

    quote_id: UUID
    response: JobModifiedDateServiceResponseResult


_LIST = Route(
    "GET",
    "/job/{jobDisplayId}/freightproviders",
    params_model="GetQuotesParams",
    response_model="List[TransportationQuoteResult]",
)
_SAVE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders",
    request_model="ShipmentPlanProvider",
    response_model="ServiceBaseResponse",
    unsupported_reason=(
        '8_01 removed provider-list writes and option indexes. Use create_final_override or '
        'save_final_quote with explicit shipping/quote identifiers.'
    ),
)
_RATE_QUOTE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders/{optionIndex}/ratequote",
    request_model="RateQuoteRequest",
    unsupported_reason=(
        '8_01 removed option-index ratequote. Use select_rate_quote with ratesKey and explicit '
        'shipping/handling units.'
    ),
)




_CURRENT_CREATE_FINAL_OVERRIDE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders/finaloverride",
    request_model="FinalOverrideRequest",
    response_model="CreateOverriddenQuoteResponseResult",
)
_CURRENT_SELECT_RATE_QUOTE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders/ratequote",
    request_model="SelectRateQuoteRequest",
    response_model="SaveRateQuoteResponseResult",
)
_CURRENT_SAVE_FINAL_QUOTE = Route(
    "POST",
    "/job/{jobDisplayId}/freightproviders/final",
    request_model="SaveFinalQuoteRequest",
    response_model="JobModifiedDateServiceResponseResult",
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

        Docs: https://ab-sdk.readthedocs.io/en/latest/migration-8-01.html
        Query params: FreightProvidersParams
        Response model: List[PricedFreightProvider]
        """
        from ab.exceptions import UnsupportedOperationError

        raise UnsupportedOperationError(
            "8_01 returns transportation quotes, not PricedFreightProvider. "
            "Use jobs.freight_providers.get_quotes with active/shipment_types filters."
        )

    def save(
        self,
        job_display_id: int,
        *,
        data: ShipmentPlanProvider | dict | list[ShipmentPlanProvider | dict],
    ) -> ServiceBaseResponse | None:
        """``POST /job/{jobDisplayId}/freightproviders``

        Retained legacy provider-list write; raises UnsupportedOperationError
        before HTTP on 8_01. Use explicit final/override/rate quote methods.

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

    def create_final_override(
        self, job_display_id: int, *, data: FinalOverrideRequest | dict
    ) -> CreateOverriddenQuoteResponseResult:
        """POST /job/{jobDisplayId}/freightproviders/finaloverride.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.create_final_override.html
        Request model: FinalOverrideRequest
        Response model: CreateOverriddenQuoteResponseResult
        """
        return self._request(_CURRENT_CREATE_FINAL_OVERRIDE.bind(jobDisplayId=job_display_id), json=data)

    def select_rate_quote(
        self, job_display_id: int, *, data: SelectRateQuoteRequest | dict
    ) -> SaveRateQuoteResponseResult:
        """POST /job/{jobDisplayId}/freightproviders/ratequote.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.select_rate_quote.html
        Request model: SelectRateQuoteRequest
        Response model: SaveRateQuoteResponseResult
        """
        return self._request(_CURRENT_SELECT_RATE_QUOTE.bind(jobDisplayId=job_display_id), json=data)

    def save_final_quote(
        self, job_display_id: int, *, data: SaveFinalQuoteRequest | dict
    ) -> JobModifiedDateServiceResponseResult:
        """POST /job/{jobDisplayId}/freightproviders/final.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.save_final_quote.html
        Request model: SaveFinalQuoteRequest
        Response model: JobModifiedDateServiceResponseResult
        """
        return self._request(_CURRENT_SAVE_FINAL_QUOTE.bind(jobDisplayId=job_display_id), json=data)

    def save_new_final_override(
        self,
        job_display_id: int,
        *,
        shipping_id: int,
        shipment_type: UUID | str,
        provider_id: UUID | str,
        provider_company_name: str,
        freight_amount: float,
        accessorial_amount: float = 0.0,
        provider_code: str | None = None,
        pro_number: str | None = None,
        quote_number: str | None = None,
        service_days: int | None = None,
        job_modified_date: datetime | str | None = None,
        handling_units: list | None = None,
    ) -> NewFinalOverride:
        """Create a final override **with its amounts** in one write.

        :meth:`create_final_override` takes no amounts, so an approval made with it
        needs a second write and can leave an active override at 0 if that write
        fails. ``POST .../freightproviders/final`` adds the posted quote when its id
        is not stored yet, so this method posts a complete override under a new id:
        the quote is created active with the given amounts and the other quotes of
        the shipping are deactivated, all in the one request.

        The shipping must exist; this call never creates one. A ``pro_number`` marks
        the override shipped (see :func:`ab.api.selection.is_recorded_override`).

        Args:
            shipping_id: Shipping the override belongs to (``jobs.shippings.get_all``).
            shipment_type: Shipment type UUID, as on an existing quote (``shipment_type``).
            provider_id: Carrier company UUID.
            provider_company_name: Name shown for the override.
            freight_amount: Carrier cost.
            accessorial_amount: Accessorial cost.
            job_modified_date: The job's modified stamp. A stale one raises
                :class:`~ab.exceptions.JobModifiedConflictError` and writes nothing.
            handling_units: When given, the shipping takes over exactly these units.

        Returns:
            ``NewFinalOverride(quote_id, response)``. ``quote_id`` is the id the new
            quote was created under; ``response.job_modified_date`` is the stamp for
            the next write.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.save_final_quote.html
        Request model: SaveFinalQuoteRequest
        Response model: JobModifiedDateServiceResponseResult
        """
        new_id = uuid4()
        quote = {
            "id": str(new_id),
            "isOverridden": True,
            "active": True,
            "shippingId": shipping_id,
            "shipmentType": str(shipment_type),
            "providerId": str(provider_id),
            "providerCompanyName": provider_company_name,
            "freightAmount": freight_amount,
            "accessorialAmount": accessorial_amount,
        }
        optional = {
            "providerCode": provider_code,
            "proNumber": pro_number,
            "quoteNumber": quote_number,
            "serviceDays": service_days,
        }
        quote.update({key: value for key, value in optional.items() if value is not None})
        data: dict = {"quote": quote}
        if job_modified_date is not None:
            data["jobModifiedDate"] = job_modified_date
        if handling_units is not None:
            data["handlingUnits"] = handling_units
        response = self.save_final_quote(job_display_id, data=data)
        return NewFinalOverride(new_id, response)

    def mark_selected(
        self,
        job_display_id: int,
        quote: TransportationQuoteResult,
        *,
        job_modified_date: datetime | str | None = None,
    ) -> JobModifiedDateServiceResponseResult:
        """Record that *quote* is a deliberate selection, not the shipping's first estimate.

        A rate selected into a shipping that had no quote (which includes every
        shipping ``select_rate_quote`` creates) is stored exactly like an estimate,
        so :func:`ab.api.selection.is_untouched_estimate` cannot tell them apart.
        This posts the quote back unchanged as the final quote of its shipping. The
        server stamps it as modified, which is what the estimate test reads; the
        amounts, PRO and accepted state are sent back as they are.

        Pass the quote as just read from :meth:`get_quotes`. Like every final-quote
        write, this leaves the quote active and deactivates the other quotes of its
        shipping.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.save_final_quote.html
        Request model: SaveFinalQuoteRequest
        Response model: JobModifiedDateServiceResponseResult
        """
        if quote.shipping_id is None:
            raise ValueError("mark_selected needs a quote that belongs to a shipping")
        data: dict = {"quote": quote.model_dump(by_alias=True, mode="json")}
        if job_modified_date is not None:
            data["jobModifiedDate"] = job_modified_date
        return self.save_final_quote(job_display_id, data=data)

    def get_quotes(
        self,
        job_display_id: int,
        *,
        shipment_types: list[UUID] | None = None,
        active: bool | None = None,
        is_overridden: bool | None = None,
        carrier_apis: list[Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20]] | None = None,
        shipped: bool | None = None,
    ) -> list[TransportationQuoteResult]:
        """GET /job/{jobDisplayId}/freightproviders.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/freight_providers.get_quotes.html
        Query params: GetQuotesParams
        Response model: List[TransportationQuoteResult]
        """
        return self._request(
            _LIST.bind(jobDisplayId=job_display_id),
            params=dict(
                shipment_types=shipment_types,
                active=active,
                is_overridden=is_overridden,
                carrier_apis=carrier_apis,
                shipped=shipped,
            ),
        )
