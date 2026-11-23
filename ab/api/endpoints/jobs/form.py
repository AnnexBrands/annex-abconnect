"""Job-scoped form generation — swagger tags ``JobForm`` + ``InvoiceJobForm`` + ``UsarJobForm`` (15 routes).

Exposed as ``api.jobs.form``. All methods were moved here from the
legacy ``api.forms`` endpoint group; :class:`~ab.api.endpoints.forms.FormsEndpoint`
remains as a deprecation shim that forwards every call to this class.

Method renames (``get_`` prefix dropped on PDF-returning routes; the JSON
route ``get_shipments`` becomes :meth:`shipments`):

* :meth:`invoice`                    (was ``get_invoice``)
* :meth:`invoice_editable`           (was ``get_invoice_editable``)
* :meth:`bill_of_lading`             (was ``get_bill_of_lading``)
* :meth:`packing_slip`               (was ``get_packing_slip``)
* :meth:`customer_quote`             (was ``get_customer_quote``)
* :meth:`quick_sale`                 (was ``get_quick_sale``)
* :meth:`operations`                 (was ``get_operations``)
* :meth:`shipments`                  (was ``get_shipments``)
* :meth:`address_label`              (was ``get_address_label``)
* :meth:`item_labels`                (was ``get_item_labels``)
* :meth:`packaging_labels`           (was ``get_packaging_labels``)
* :meth:`packaging_specification`    (was ``get_packaging_specification``)
* :meth:`credit_card_authorization`  (was ``get_credit_card_authorization``)
* :meth:`usar`                       (was ``get_usar``)
* :meth:`usar_editable`              (was ``get_usar_editable``)

Convenience helpers (``bol``, ``hbl``, ``pbl``, ``dbl``, ``ops``) are
retained on this class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ab.api.base import BaseEndpoint
from ab.api.models.release_support import EditableFormContent, ShipmentFormPlan
from ab.api.route import Route
from ab.warnings import warn_legacy_request

if TYPE_CHECKING:
    from ab.api.models.forms import FormsShipmentPlan


_INVOICE = Route("GET", "/job/{jobDisplayId}/form/invoice", params_model="FormTypeParams", response_model="bytes")
_INVOICE_EDITABLE = Route("GET", "/job/{jobDisplayId}/form/invoice/editable", response_model="EditableFormContent")
_BOL = Route(
    "GET", "/job/{jobDisplayId}/form/bill-of-lading", params_model="ShipmentBillOfLadingParams", response_model="bytes"
)
_PACKING_SLIP = Route(
    "GET", "/job/{jobDisplayId}/form/packing-slip", params_model="FormQuoteParams", response_model="bytes"
)
_CUSTOMER_QUOTE = Route("GET", "/job/{jobDisplayId}/form/customer-quote", response_model="bytes")
_QUICK_SALE = Route("GET", "/job/{jobDisplayId}/form/quick-sale", response_model="bytes")
_OPERATIONS = Route(
    "GET", "/job/{jobDisplayId}/form/operations", params_model="OperationsFormParams", response_model="bytes"
)
_SHIPMENTS = Route("GET", "/job/{jobDisplayId}/form/shipments", response_model="List[ShipmentFormPlan]")
_ADDRESS_LABEL = Route("GET", "/job/{jobDisplayId}/form/address-label", response_model="bytes")
_ITEM_LABELS = Route("GET", "/job/{jobDisplayId}/form/item-labels", response_model="bytes")
_PACKAGING_LABELS = Route(
    "GET", "/job/{jobDisplayId}/form/packaging-labels", params_model="PackagingLabelsParams", response_model="bytes"
)
_PACKAGING_SPEC = Route(
    "GET", "/job/{jobDisplayId}/form/packaging-specification", params_model="FormQuoteParams", response_model="bytes"
)
_CC_AUTH = Route("GET", "/job/{jobDisplayId}/form/credit-card-authorization", response_model="bytes")
_USAR = Route("GET", "/job/{jobDisplayId}/form/usar", params_model="FormTypeParams", response_model="bytes")
_USAR_EDITABLE = Route("GET", "/job/{jobDisplayId}/form/usar/editable", response_model="EditableFormContent")


class JobFormEndpoint(BaseEndpoint):
    """Job-scoped form generation (ACPortal API).

    Most methods return ``{filename: bytes}`` (PDF content). Use
    :meth:`shipments` to get JSON shipment plan data for BOL selection.
    """

    def _pdf(self, route: Route, job_display_id: int, name: str, **kw: Any) -> dict[str, bytes]:
        data = self._request(route.bind(jobDisplayId=job_display_id), **kw)
        return {f"{name}_{job_display_id}.pdf": data}

    # ------------------------------------------------------------------
    # JSON route (shipment-plan discovery)
    # ------------------------------------------------------------------

    def shipments(self, job_display_id: int) -> list[ShipmentFormPlan]:
        """List shipment plans for *job_display_id* (``GET /job/{jobDisplayId}/form/shipments``).

        Returns ``List[FormsShipmentPlan]`` rather than PDF bytes -- use the
        ``job_shipment_id`` of a plan to drive the BOL routes below.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/form.shipments.html
        Response model: List[ShipmentFormPlan]
        """
        return self._request(_SHIPMENTS.bind(jobDisplayId=job_display_id))

    # ------------------------------------------------------------------
    # PDF routes
    # ------------------------------------------------------------------

    def invoice(self, job_display_id: int, *, type: Optional[str] = None) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/invoice``"""
        return self._pdf(_INVOICE, job_display_id, "invoice", params=dict(type=type))

    def invoice_editable(self, job_display_id: int) -> EditableFormContent:
        """``GET /job/{jobDisplayId}/form/invoice/editable``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/form.invoice_editable.html
        Response model: EditableFormContent
        """
        return self._request(_INVOICE_EDITABLE.bind(jobDisplayId=job_display_id))

    def bill_of_lading(
        self,
        job_display_id: int,
        *,
        shipment_plan_id: Optional[str] = None,
        provider_option_index: Optional[int] = None,
        quote_id: Optional[str] = None,
    ) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/bill-of-lading``"""
        if provider_option_index is not None:
            from ab.exceptions import UnsupportedOperationError

            raise UnsupportedOperationError("8_01 BOL requires quote_id; option indexes cannot identify a quote.")
        if quote_id is None:
            warn_legacy_request("jobs.form.bill_of_lading()", "jobs.form.bill_of_lading(quote_id=...)")
        return self._pdf(
            _BOL,
            job_display_id,
            "bol",
            params=dict(shipment_plan_id=shipment_plan_id, quote_id=quote_id),
        )

    def packing_slip(self, job_display_id: int, *, quote_id: Optional[str] = None) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/packing-slip``

        Set ``quote_id`` to select a shipment's quote on 8_01. Omitting it
        preserves the server's job-level behavior.

        Query params: FormQuoteParams
        """
        if quote_id is None:
            warn_legacy_request("jobs.form.packing_slip()", "jobs.form.packing_slip(quote_id=...)")
        return self._pdf(_PACKING_SLIP, job_display_id, "packing_slip", params=dict(quote_id=quote_id))

    def customer_quote(self, job_display_id: int) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/customer-quote``"""
        return self._pdf(_CUSTOMER_QUOTE, job_display_id, "customer_quote")

    def quick_sale(self, job_display_id: int) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/quick-sale``"""
        return self._pdf(_QUICK_SALE, job_display_id, "quick_sale")

    def operations(
        self, job_display_id: int, *, ops_type: Optional[str] = None, quote_id: str | None = None
    ) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/operations``"""
        if quote_id is None:
            warn_legacy_request("jobs.form.operations()", "jobs.form.operations(quote_id=...)")
        return self._pdf(_OPERATIONS, job_display_id, "operations", params=dict(ops_type=ops_type, quote_id=quote_id))

    def address_label(self, job_display_id: int) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/address-label``"""
        return self._pdf(_ADDRESS_LABEL, job_display_id, "address_label")

    def item_labels(self, job_display_id: int) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/item-labels``"""
        return self._pdf(_ITEM_LABELS, job_display_id, "item_labels")

    def packaging_labels(
        self,
        job_display_id: int,
        *,
        shipment_plan_id: Optional[str] = None,
    ) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/packaging-labels``"""
        return self._pdf(
            _PACKAGING_LABELS,
            job_display_id,
            "packaging_labels",
            params=dict(shipment_plan_id=shipment_plan_id),
        )

    def packaging_specification(self, job_display_id: int, *, quote_id: Optional[str] = None) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/packaging-specification``

        Set ``quote_id`` to select a shipment's quote on 8_01. Omitting it
        preserves the server's job-level behavior.

        Query params: FormQuoteParams
        """
        if quote_id is None:
            warn_legacy_request(
                "jobs.form.packaging_specification()",
                "jobs.form.packaging_specification(quote_id=...)",
            )
        return self._pdf(_PACKAGING_SPEC, job_display_id, "packaging_spec", params=dict(quote_id=quote_id))

    def credit_card_authorization(self, job_display_id: int) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/credit-card-authorization``"""
        return self._pdf(_CC_AUTH, job_display_id, "cc_auth")

    def usar(self, job_display_id: int, *, type: Optional[str] = None) -> dict[str, bytes]:
        """``GET /job/{jobDisplayId}/form/usar``"""
        return self._pdf(_USAR, job_display_id, "usar", params=dict(type=type))

    def usar_editable(self, job_display_id: int) -> EditableFormContent:
        """``GET /job/{jobDisplayId}/form/usar/editable``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/form.usar_editable.html
        Response model: EditableFormContent
        """
        return self._request(_USAR_EDITABLE.bind(jobDisplayId=job_display_id))

    # ------------------------------------------------------------------
    # Convenience helpers (transport-type aware BOL selection)
    # ------------------------------------------------------------------

    @staticmethod
    def _leg(plan: FormsShipmentPlan) -> tuple[str, str]:
        """Split a plan's ``transport_type`` into (leg, carrier mode).

        8_01 names the carrier leg after its mode, e.g. ``"PickUp (LTL)"`` or
        ``"PickUp (PARCEL)"``; the agent legs and the house row are plain
        (``"PickUp"``, ``"Delivery"``, ``"House"``). 7_11 used ``"LTL"`` alone.
        """
        text = (plan.transport_type or "").strip()
        if text.endswith(")") and " (" in text:
            leg, mode = text[:-1].split(" (", 1)
            return leg.strip(), mode.strip().upper()
        if text.upper() == "LTL":
            return "PickUp", "LTL"
        return text, ""

    def _select_plan(self, job_display_id: int, *, leg: str, carrier: bool, quote_id: str | None):
        """The single shipment plan for *leg*; for the carrier leg, the one joined to *quote_id*."""
        plans = [
            p for p in self.shipments(job_display_id)
            if self._leg(p)[0].casefold() == leg.casefold() and bool(self._leg(p)[1]) == carrier
        ]
        if carrier and quote_id is not None:
            wanted = str(quote_id).casefold()
            plans = [p for p in plans if str(p.freight_quote_options_id or "").casefold() == wanted] or plans
        # The server lists the carrier leg once per active quote of the job.
        if len({str(p.job_shipment_id) for p in plans}) != 1 or (carrier and quote_id is None and len(plans) != 1):
            raise ValueError(
                f"Expected exactly one {leg} shipment plan for job {job_display_id}, found {len(plans)}. "
                "Use bill_of_lading with explicit shipment_plan_id and quote_id."
            )
        return plans[0]

    def _bol_for(self, job_display_id: int, prefix: str, plan: FormsShipmentPlan, quote_id: str | None):
        if quote_id is None:
            quote_id = plan.freight_quote_options_id if self._leg(plan)[1] else None
        if quote_id is None:
            warn_legacy_request(f"jobs.form.{prefix}()", f"jobs.form.{prefix}(quote_id=...)")
        return self._pdf(
            _BOL,
            job_display_id,
            prefix,
            params=dict(shipment_plan_id=str(plan.job_shipment_id), quote_id=str(quote_id) if quote_id else None),
        )

    def ops(self, job_display_id: int, *, ops_type: str | None = None, quote_id: str | None = None) -> dict[str, bytes]:
        """Alias for :meth:`operations` that prefixes the PDF filename with ``ops_``."""
        result = self.operations(job_display_id, ops_type=ops_type, quote_id=quote_id)
        return {f"ops_{job_display_id}.pdf": next(iter(result.values()))}

    def bol(self, job_display_id: int, *, quote_id: str | None = None) -> dict[str, bytes]:
        """Carrier BOL for the job's carrier leg.

        With ``quote_id`` the document is that quote's: its carrier, PRO and the
        handling units of its shipping. Without it the helper uses the one active
        quote the carrier leg is joined to, and raises when a job has several
        (name the quote). A document rendered with no quote at all is a
        non-carrier BOL listing the job's inventory, not a shipping's units.
        """
        plan = self._select_plan(job_display_id, leg="PickUp", carrier=True, quote_id=quote_id)
        return self._bol_for(job_display_id, "bol", plan, quote_id)

    def hbl(self, job_display_id: int, *, quote_id: str | None = None) -> dict[str, bytes]:
        """House Bill of Lading."""
        plan = self._select_plan(job_display_id, leg="House", carrier=False, quote_id=None)
        return self._bol_for(job_display_id, "hbl", plan, quote_id)

    def pbl(self, job_display_id: int, *, quote_id: str | None = None) -> dict[str, bytes]:
        """Pickup Bill of Lading (the pickup agent's leg, not the carrier's)."""
        plan = self._select_plan(job_display_id, leg="PickUp", carrier=False, quote_id=None)
        return self._bol_for(job_display_id, "pbl", plan, quote_id)

    def dbl(self, job_display_id: int, *, quote_id: str | None = None) -> dict[str, bytes]:
        """Delivery Bill of Lading (only valid when an LTL carrier leg exists)."""
        if not any(self._leg(p)[1] == "LTL" for p in self.shipments(job_display_id)):
            raise ValueError("No LTL shipment plan exists -- Delivery BOL not applicable")
        plan = self._select_plan(job_display_id, leg="Delivery", carrier=False, quote_id=None)
        return self._bol_for(job_display_id, "dbl", plan, quote_id)
