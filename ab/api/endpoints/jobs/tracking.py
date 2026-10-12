"""Job-scoped tracking operations — swagger tag ``JobTracking`` (3 routes).

Exposed as ``api.jobs.tracking``. Old names on
:class:`~ab.api.endpoints.jobs.JobsEndpoint` remain as deprecation shims.

Method renames (``get_tracking`` collapsed):

* :meth:`get`     (was ``get_tracking``)        — ``GET /job/{id}/tracking``
* :meth:`v3`      (was ``get_tracking_v3``)     — ``GET /v3/job/{id}/tracking/{historyAmount}``

The ``v3`` route lives under ``/v3/`` (not ``/job/{id}/tracking/``)
because it's a separate versioned controller; both methods are tagged
``JobTracking`` in swagger.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ab.api.base import BaseEndpoint
from ab.api.models.release_support import (
    CarrierShipmentDetails,
    ShipmentTrackingDocumentResult,
)
from ab.api.route import Route
from ab.warnings import warn_legacy_request

if TYPE_CHECKING:
    from ab.api.models.jobs import ShipmentTrackingDetails, TrackingInfo, TrackingInfoV3


_GET = Route(
    "GET",
    "/job/{jobDisplayId}/tracking",
    response_model="TrackingInfo",
    unsupported_reason="8_01 removed unversioned job tracking. Use jobs.tracking.v3 or shipment with quote_id.",
)
_GET_V3 = Route(
    "GET",
    "/v3/job/{jobDisplayId}/tracking/{historyAmount}",
    response_model="TrackingInfoV3",
    params_model="TrackingV3Params",
)
_SHIPMENT = Route(
    "GET",
    "/job/{jobDisplayId}/tracking/shipment/{proNumber}",
    response_model="ShipmentTrackingDetails",
    params_model="ShipmentTrackingParams",
)




_CURRENT_SHIPMENT_HISTORY = Route(
    "GET",
    "/job/{jobDisplayId}/tracking/shipment-history/{proNumber}",
    response_model="CarrierShipmentDetails",
    params_model="ShipmentHistoryParams",
)
_CURRENT_SHIPMENT_DOCUMENTS = Route(
    "GET",
    "/job/{jobDisplayId}/tracking/shipment-documents/{proNumber}",
    response_model="List[ShipmentTrackingDocumentResult]",
    params_model="ShipmentDocumentsParams",
)


class JobTrackingEndpoint(BaseEndpoint):
    """Job-scoped tracking operations (ACPortal API)."""

    def get(self, job_display_id: int) -> TrackingInfo:
        """``GET /job/{jobDisplayId}/tracking``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/tracking.get.html
        Response model: TrackingInfo
        """
        return self._request(_GET.bind(jobDisplayId=job_display_id))

    def v3(self, job_display_id: int, history_amount: int = 10) -> TrackingInfoV3:
        """``GET /v3/job/{jobDisplayId}/tracking/{historyAmount}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/tracking.v3.html
        Path params: TrackingV3Params
        Response model: TrackingInfoV3
        """
        return self._request(
            _GET_V3.bind(jobDisplayId=job_display_id, historyAmount=history_amount),
        )

    def shipment(
        self,
        job_display_id: int,
        pro_number: str,
        *,
        quote_id: str | None = None,
    ) -> ShipmentTrackingDetails:
        """``GET /job/{jobDisplayId}/tracking/shipment/{proNumber}``

        Tracking detail for ONE shipment of the job, looked up by its
        carrier PRO number — carrier statuses, weights, packages, and any
        attached tracking documents.

        Args:
            job_display_id: Job display ID the shipment belongs to.
            pro_number: Carrier PRO number of the shipment.
            quote_id: Quote UUID identifying the shipment on 8_01. Omit to
                retain the existing PRO-based lookup.

        Response model: ShipmentTrackingDetails

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/tracking.shipment.html
        Query params: ShipmentTrackingParams
        Response model: ShipmentTrackingDetails
        """
        if quote_id is None:
            warn_legacy_request("jobs.tracking.shipment()", "jobs.tracking.shipment(quote_id=...)")
        return self._request(
            _SHIPMENT.bind(jobDisplayId=job_display_id, proNumber=pro_number),
            params=dict(quote_id=quote_id),
        )

    def shipment_history(
        self, job_display_id: int, pro_number: str, *, quote_id: UUID | None = None
    ) -> CarrierShipmentDetails:
        """GET /job/{jobDisplayId}/tracking/shipment-history/{proNumber}.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/tracking.shipment_history.html
        Query params: ShipmentHistoryParams
        Response model: CarrierShipmentDetails
        """
        return self._request(
            _CURRENT_SHIPMENT_HISTORY.bind(jobDisplayId=job_display_id, proNumber=pro_number),
            params=dict(quote_id=quote_id),
        )

    def shipment_documents(
        self, job_display_id: int, pro_number: str, *, quote_id: UUID | None = None
    ) -> list[ShipmentTrackingDocumentResult]:
        """GET /job/{jobDisplayId}/tracking/shipment-documents/{proNumber}.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/tracking.shipment_documents.html
        Query params: ShipmentDocumentsParams
        Response model: List[ShipmentTrackingDocumentResult]
        """
        return self._request(
            _CURRENT_SHIPMENT_DOCUMENTS.bind(jobDisplayId=job_display_id, proNumber=pro_number),
            params=dict(quote_id=quote_id),
        )
