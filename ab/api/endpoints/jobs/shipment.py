"""Job-scoped shipment operations — swagger tag ``JobShipment`` (11 routes).

Exposed as ``api.jobs.shipment``. The legacy ``api.shipments``
endpoint retains the 3 non-job-scoped routes (``GET /shipment``,
``GET /shipment/accessorials``, ``GET /shipment/document/{docId}``); the
11 job-scoped routes move here and ``api.shipments`` keeps deprecation
shims that forward to this class.

Method renames (drop redundant ``_shipment`` suffix; standardise ``get_``):

* :meth:`get_rate_quotes`         (unchanged)
* :meth:`request_rate_quotes`     (unchanged)
* :meth:`book`                    (unchanged)
* :meth:`delete`                  (was ``delete_shipment``)
* :meth:`get_accessorials`        (unchanged)
* :meth:`add_accessorial`         (unchanged)
* :meth:`remove_accessorial`      (unchanged)
* :meth:`get_origin_destination`  (unchanged)
* :meth:`get_export_data`         (unchanged)
* :meth:`post_export_data`        (unchanged)
* :meth:`get_rates_state`         (unchanged)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ab.api.base import BaseEndpoint
from ab.api.endpoints.jobs.shippings import JobShippingsEndpoint
from ab.api.models.transportation import (
    BookingValidationResult,
    ShipmentBookingResult,
    ShipmentCancelResult,
    ShippingExportData,
)
from ab.api.route import Route
from ab.api.selection import quote_id as validate_quote_id
from ab.api.selection import select_shipping
from ab.api.selection import shipping_id as validate_shipping_id
from ab.warnings import warn_legacy_request

if TYPE_CHECKING:
    from ab.api.models.shared import ServiceBaseResponse
    from ab.api.models.shipments import (
        Accessorial,
        AccessorialAddRequest,
        JobCarrierRates,
        RateQuote,
        RatesState,
        ShipmentBookRequest,
        ShipmentExportData,
        ShipmentExportRequest,
        ShipmentOriginDestination,
        ShipmentRateQuoteRequest,
    )


_GET_RATE_QUOTES = Route(
    "GET",
    "/job/{jobDisplayId}/shipment/ratequotes",
    params_model="RateQuotesParams",
    response_model="List[RateQuote]",
    unsupported_reason=(
        '8_01 removed legacy ratequotes. Use jobs.rates.request with explicit handling units and '
        'addresses, then jobs.rates.select_quote.'
    ),
)
_POST_RATE_QUOTES = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/ratequotes",
    request_model="ShipmentRateQuoteRequest",
    response_model="List[RateQuote]",
    unsupported_reason=(
        '8_01 removed legacy ratequotes. Use jobs.rates.request with explicit handling units and '
        'addresses, then jobs.rates.select_quote.'
    ),
)
_BOOK = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/book",
    request_model="ShipmentBookRequest",
    response_model="ServiceBaseResponse",
)
_DELETE = Route("DELETE", "/job/{jobDisplayId}/shipment", response_model="ServiceBaseResponse")
_GET_ACCESSORIALS = Route(
    "GET",
    "/job/{jobDisplayId}/shipment/accessorials",
    response_model="List[Accessorial]",
    unsupported_reason=(
        '8_01 replaced shipment accessorials. Use jobs.add_ons with the current service add-on '
        'identifiers.'
    ),
)
_ADD_ACCESSORIAL = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/accessorial",
    request_model="AccessorialAddRequest",
    response_model="ServiceBaseResponse",
    unsupported_reason=(
        '8_01 replaced shipment accessorials. Use jobs.add_ons with the current service add-on '
        'identifiers.'
    ),
)
_REMOVE_ACCESSORIAL = Route(
    "DELETE",
    "/job/{jobDisplayId}/shipment/accessorial/{addOnId}",
    response_model="ServiceBaseResponse",
    unsupported_reason=(
        '8_01 replaced shipment accessorials. Use jobs.add_ons with the current service add-on '
        'identifiers.'
    ),
)
_GET_ORIGIN_DEST = Route(
    "GET",
    "/job/{jobDisplayId}/shipment/origindestination",
    response_model="ShipmentOriginDestination",
)
_GET_EXPORT_DATA = Route("GET", "/job/{jobDisplayId}/shipment/exportdata", response_model="ShipmentExportData")
_POST_EXPORT_DATA = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/exportdata",
    request_model="ShipmentExportRequest",
    response_model="ServiceBaseResponse",
)
_GET_RATES_STATE = Route("GET", "/job/{jobDisplayId}/shipment/ratesstate", response_model="RatesState")


_BOOK_V2 = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/v2/book",
    request_model="BookShipmentRequestV2",
    response_model="ShipmentBookingResult",
)
_VALIDATE = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/validate",
    request_model="BookShipmentRequestV2",
    response_model="BookingValidationResult",
)
_CANCEL = Route(
    "PUT",
    "/job/{jobDisplayId}/shipment/cancel/{quoteId}",
    request_model="CancelShipmentRequest",
    response_model="ShipmentCancelResult",
)
_GET_SHIPPING_EXPORT = Route(
    "GET",
    "/job/{jobDisplayId}/shipment/exportdata/{shippingId}",
    response_model="ShippingExportData",
)
_SAVE_SHIPPING_EXPORT = Route(
    "POST",
    "/job/{jobDisplayId}/shipment/exportdata/{shippingId}",
    request_model="ShippingExportRequest",
)


class JobShipmentEndpoint(BaseEndpoint):
    """Job-scoped shipment operations (ACPortal API)."""

    def get_rate_quotes(self, job_display_id: int) -> list[RateQuote]:
        """``GET /job/{jobDisplayId}/shipment/ratequotes``

        Compatibility list view over ``JobCarrierRates.rates``. Use
        :meth:`get_rate_quotes_result` when you need ``ratesKey``,
        ``requestSnapshot``, or ``errors``.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_rate_quotes.html
        Query params: RateQuotesParams
        Response model: List[RateQuote]
        """
        return self._request(_GET_RATE_QUOTES.bind(jobDisplayId=job_display_id))

    def request_rate_quotes(self, job_display_id: int, *, data: ShipmentRateQuoteRequest | dict) -> list[RateQuote]:
        """``POST /job/{jobDisplayId}/shipment/ratequotes``

        Compatibility list view over ``JobCarrierRates.rates``. Use
        :meth:`request_rate_quotes_result` when you need ``ratesKey``,
        ``requestSnapshot``, or ``errors``.

        Request model: :class:`ShipmentRateQuoteRequest`.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.request_rate_quotes.html
        Request model: ShipmentRateQuoteRequest
        Response model: List[RateQuote]
        """
        return self._request(_POST_RATE_QUOTES.bind(jobDisplayId=job_display_id), json=data)

    def get_rate_quotes_result(self, job_display_id: int) -> JobCarrierRates:
        """``GET /job/{jobDisplayId}/shipment/ratequotes``

        Returns the full API 7.11 ``JobCarrierRates`` envelope, including the
        ``ratesKey`` needed by booking flows and any quote errors.

        Response model: JobCarrierRates
        """
        _GET_RATE_QUOTES.ensure_supported()
        route = _GET_RATE_QUOTES.bind(jobDisplayId=job_display_id)
        response = self._client.request(route.method, route.path)
        return self._coerce_rate_quotes_result(response)

    def request_rate_quotes_result(
        self,
        job_display_id: int,
        *,
        data: ShipmentRateQuoteRequest | dict,
    ) -> JobCarrierRates:
        """``POST /job/{jobDisplayId}/shipment/ratequotes``

        Returns the full API 7.11 ``JobCarrierRates`` envelope, including the
        ``ratesKey`` needed by booking flows and any quote errors.

        Request model: :class:`ShipmentRateQuoteRequest`.

        Request model: ShipmentRateQuoteRequest
        Response model: JobCarrierRates
        """
        _POST_RATE_QUOTES.ensure_supported()
        payload = self._resolve_model(_POST_RATE_QUOTES.request_model).check(data)
        route = _POST_RATE_QUOTES.bind(jobDisplayId=job_display_id)
        response = self._client.request(route.method, route.path, json=payload)
        return self._coerce_rate_quotes_result(response)

    @staticmethod
    def _coerce_rate_quotes_result(response: object) -> JobCarrierRates:
        from ab.api.models.shipments import JobCarrierRates

        if response is None:
            return JobCarrierRates()
        if isinstance(response, list):
            return JobCarrierRates(rates=response)
        return JobCarrierRates.model_validate(response)

    def _require_single_shipping(self, job_display_id: int) -> None:
        """Guard legacy mutations against ambiguous job-level selection."""
        select_shipping(JobShippingsEndpoint(self._client).get_all(job_display_id))

    def book(self, job_display_id: int, *, data: ShipmentBookRequest | dict) -> ServiceBaseResponse:
        """``POST /job/{jobDisplayId}/shipment/book``

        Request model: :class:`ShipmentBookRequest`.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.book.html
        Request model: ShipmentBookRequest
        Response model: ServiceBaseResponse
        """
        warn_legacy_request("jobs.shipment.book()", "jobs.shipment.book_v2(quote_id=...)")
        payload = self._resolve_model(_BOOK.request_model).check(data)
        if "quoteOptionIndex" in payload:
            raise ValueError(
                "8_01 no longer accepts quoteOptionIndex; use book_v2(quote_id=...) "
                "with a quote from jobs.shippings.get_all()."
            )
        self._require_single_shipping(job_display_id)
        return self._request(_BOOK.bind(jobDisplayId=job_display_id), json=payload)

    def delete(self, job_display_id: int) -> ServiceBaseResponse:
        """``DELETE /job/{jobDisplayId}/shipment``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.delete.html
        Response model: ServiceBaseResponse
        """
        warn_legacy_request("jobs.shipment.delete()", "jobs.shipment.cancel(quote_id=...)")
        self._require_single_shipping(job_display_id)
        return self._request(_DELETE.bind(jobDisplayId=job_display_id), json={"forceDelete": False})

    def get_accessorials(self, job_display_id: int) -> list[Accessorial]:
        """``GET /job/{jobDisplayId}/shipment/accessorials``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_accessorials.html
        Response model: List[Accessorial]
        """
        return self._request(_GET_ACCESSORIALS.bind(jobDisplayId=job_display_id))

    def add_accessorial(self, job_display_id: int, *, data: AccessorialAddRequest | dict) -> ServiceBaseResponse:
        """``POST /job/{jobDisplayId}/shipment/accessorial``

        Request model: :class:`AccessorialAddRequest`.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.add_accessorial.html
        Request model: AccessorialAddRequest
        Response model: ServiceBaseResponse
        """
        return self._request(_ADD_ACCESSORIAL.bind(jobDisplayId=job_display_id), json=data)

    def remove_accessorial(self, job_display_id: int, add_on_id: str) -> ServiceBaseResponse:
        """``DELETE /job/{jobDisplayId}/shipment/accessorial/{addOnId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.remove_accessorial.html
        Response model: ServiceBaseResponse
        """
        return self._request(
            _REMOVE_ACCESSORIAL.bind(jobDisplayId=job_display_id, addOnId=add_on_id),
        )

    def get_origin_destination(self, job_display_id: int) -> ShipmentOriginDestination:
        """``GET /job/{jobDisplayId}/shipment/origindestination``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_origin_destination.html
        Response model: ShipmentOriginDestination
        """
        return self._request(_GET_ORIGIN_DEST.bind(jobDisplayId=job_display_id))

    def get_export_data(self, job_display_id: int) -> ShipmentExportData:
        """``GET /job/{jobDisplayId}/shipment/exportdata``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_export_data.html
        Response model: ShipmentExportData
        """
        warn_legacy_request(
            "jobs.shipment.get_export_data()",
            "jobs.shipment.get_shipping_export_data(shipping_id=...)",
        )
        return self._request(_GET_EXPORT_DATA.bind(jobDisplayId=job_display_id))

    def post_export_data(self, job_display_id: int, *, data: ShipmentExportRequest | dict) -> ServiceBaseResponse:
        """``POST /job/{jobDisplayId}/shipment/exportdata``

        The body is the portal's flat ``InternationalParams`` shape —
        :class:`ShipmentExportRequest`, ``customsValue`` required. In 8_01,
        commodity ``jobItemId`` is accepted and retained when saving. A single
        active shipping record is required for this legacy job-level write.
        Use :meth:`save_shipping_export_data` for explicit shipment selection.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.post_export_data.html
        Request model: ShipmentExportRequest
        Response model: ServiceBaseResponse
        """
        warn_legacy_request(
            "jobs.shipment.post_export_data()",
            "jobs.shipment.save_shipping_export_data(shipping_id=...)",
        )
        payload = self._resolve_model(_POST_EXPORT_DATA.request_model).check(data)
        self._require_single_shipping(job_display_id)
        return self._request(_POST_EXPORT_DATA.bind(jobDisplayId=job_display_id), json=payload)

    def get_rates_state(self, job_display_id: int) -> RatesState:
        """``GET /job/{jobDisplayId}/shipment/ratesstate``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_rates_state.html
        Response model: RatesState
        """
        warn_legacy_request("jobs.shipment.get_rates_state()", "jobs.shippings.get_all()")
        return self._request(_GET_RATES_STATE.bind(jobDisplayId=job_display_id))

    def book_v2(self, job_display_id: int, **kwargs: Any) -> ShipmentBookingResult:
        """Book one explicit ``quote_id`` using the 8_01 contract.

        Supply the last observed ``job_modified_date`` for conflict detection.
        ``shipment_id`` in the result is a carrier ID, not a shipping record ID.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.book_v2.html
        Request model: BookShipmentRequestV2
        Response model: ShipmentBookingResult
        """
        return self._request(_BOOK_V2.bind(jobDisplayId=job_display_id), json=kwargs)

    def validate(self, job_display_id: int, **kwargs: Any) -> BookingValidationResult:
        """Validate an explicit ``quote_id`` and booking fields before booking.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.validate.html
        Request model: BookShipmentRequestV2
        Response model: BookingValidationResult
        """
        return self._request(_VALIDATE.bind(jobDisplayId=job_display_id), json=kwargs)

    def cancel(self, job_display_id: int, quote_id: str, **kwargs: Any) -> ShipmentCancelResult:
        """Cancel the shipment identified by a quote UUID; preserves other shipments.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.cancel.html
        Request model: CancelShipmentRequest
        Response model: ShipmentCancelResult
        """
        return self._request(
            _CANCEL.bind(jobDisplayId=job_display_id, quoteId=validate_quote_id(quote_id)),
            json=kwargs,
        )

    def get_shipping_export_data(self, job_display_id: int, shipping_id: int) -> ShippingExportData | None:
        """Read export data for an explicit integer ``Shipping.id``.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.get_shipping_export_data.html
        Response model: ShippingExportData
        """
        return self._request(
            _GET_SHIPPING_EXPORT.bind(jobDisplayId=job_display_id, shippingId=validate_shipping_id(shipping_id)),
        )

    def save_shipping_export_data(self, job_display_id: int, shipping_id: int, **kwargs: Any) -> None:
        """Save current export fields, including commodity IDs, for one shipping record.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/shipment.save_shipping_export_data.html
        Request model: ShippingExportRequest
        """
        return self._request(
            _SAVE_SHIPPING_EXPORT.bind(jobDisplayId=job_display_id, shippingId=validate_shipping_id(shipping_id)),
            json=kwargs,
        )
