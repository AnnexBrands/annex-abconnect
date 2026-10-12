"""Typed 8_01 transportation contracts from release controllers and staging schema.

Request and response types are separate: outbound nested objects reject unknown
keys, while responses retain and report newly introduced server fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from ab.api.models.base import ResponseModel
from ab.api.models.packing import PackingRequestModel


class ExportDataCommodityInput(PackingRequestModel):
    """ExportDataCommodity request contract (8_01)."""

    description: str | None = Field(default=None, alias="description", description="Description.")
    weight: float = Field(alias="weight", description="Weight.")
    unit_price: float = Field(alias="unitPrice", description="Unit price.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")
    country_iata_code: str | None = Field(default=None, alias="countryIATACode", description="Country iata code.")
    quantity: float = Field(alias="quantity", description="Quantity.")
    unit_of_measure: str | None = Field(default=None, alias="unitOfMeasure", description="Unit of measure.")
    schedule_b_number: str | None = Field(default=None, alias="scheduleBNumber", description="Schedule b number.")
    eccn: str | None = Field(default=None, alias="eccn", description="Eccn.")
    export_license_code: str | None = Field(default=None, alias="exportLicenseCode", description="Export license code.")
    special_marks: str | None = Field(default=None, alias="specialMarks", description="Special marks.")
    item_value: float | None = Field(default=None, alias="itemValue", description="Item value.")
    job_item_id: UUID | None = Field(
        default=None,
        alias="jobItemId",
        description="Export commodity item UUID; retained on GET/edit/POST round trips.",
    )


class ExportPackingInfoInput(PackingRequestModel):
    """ExportPackingInfo request contract (8_01)."""

    commodity: int | None = Field(default=None, alias="commodity", description="Commodity.")
    package: str | None = Field(default=None, alias="package", description="Package.")
    package_number: int | None = Field(default=None, alias="packageNumber", description="Package number.")
    amount_in_package: int | None = Field(default=None, alias="amountInPackage", description="Amount in package.")


class ExportTotalCostsInput(PackingRequestModel):
    """ExportTotalCosts request contract (8_01)."""

    discount: float | None = Field(default=None, alias="discount", description="Discount.")
    insurance: float | None = Field(default=None, alias="insurance", description="Insurance.")
    freight: float | None = Field(default=None, alias="freight", description="Freight.")
    packing: float | None = Field(default=None, alias="packing", description="Packing.")
    handling: float | None = Field(default=None, alias="handling", description="Handling.")
    other: float | None = Field(default=None, alias="other", description="Other.")


class SoldToAddressInput(PackingRequestModel):
    """SoldToAddress request contract (8_01)."""

    address_line1: str | None = Field(default=None, alias="addressLine1", description="Address line1.")
    address_line2: str | None = Field(default=None, alias="addressLine2", description="Address line2.")
    city: str | None = Field(default=None, alias="city", description="City.")
    state: str | None = Field(default=None, alias="state", description="State.")
    zip_code: str | None = Field(default=None, alias="zipCode", description="Zip code.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")


class SoldToDetailsInput(PackingRequestModel):
    """SoldToDetails request contract (8_01)."""

    contact_name: str | None = Field(default=None, alias="contactName", description="Contact name.")
    company_name: str | None = Field(default=None, alias="companyName", description="Company name.")
    phone_number: str | None = Field(default=None, alias="phoneNumber", description="Phone number.")
    email_address: str | None = Field(default=None, alias="emailAddress", description="Email address.")
    address: SoldToAddressInput | None = Field(default=None, alias="address", description="Address.")
    tax_id: str | None = Field(default=None, alias="taxId", description="Tax id.")


class USPSSpecificInput(PackingRequestModel):
    """USPSSpecific request contract (8_01)."""

    aesitn: str | None = Field(default=None, alias="aesitn", description="Aesitn.")
    content_comments: str | None = Field(default=None, alias="contentComments", description="Content comments.")
    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")


class FedExSpecificInput(PackingRequestModel):
    """FedExSpecific request contract (8_01)."""

    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")
    special_instructions: str | None = Field(
        default=None, alias="specialInstructions", description="Special instructions."
    )
    payment_type: str | None = Field(default=None, alias="paymentType", description="Payment type.")
    export_compliance_statement: str | None = Field(
        default=None, alias="exportComplianceStatement", description="Export compliance statement."
    )


class UPSSpecificInput(PackingRequestModel):
    """UPSSpecific request contract (8_01)."""

    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")
    shipper_memo: str | None = Field(default=None, alias="shipperMemo", description="Shipper memo.")
    invoice_date: datetime | None = Field(default=None, alias="invoiceDate", description="Invoice date.")
    duties_paid_by_sender: bool = Field(default=False, alias="dutiesPaidBySender", description="Duties paid by sender.")
    description_on_label: str | None = Field(
        default=None, alias="descriptionOnLabel", description="Description on label."
    )
    exemption_or_itn: str | None = Field(default=None, alias="exemptionOrITN", description="Exemption or itn.")


class JobExportDataInput(PackingRequestModel):
    """JobExportData request contract (8_01)."""

    commodities: list[ExportDataCommodityInput] | None = Field(
        default=None, alias="commodities", description="Commodities."
    )
    packing_info: list[ExportPackingInfoInput] | None = Field(
        default=None, alias="packingInfo", description="Packing info."
    )
    customs_value: float = Field(alias="customsValue", description="Customs value.")
    invoice_number: str | None = Field(default=None, alias="invoiceNumber", description="Invoice number.")
    purchase_order_number: str | None = Field(
        default=None, alias="purchaseOrderNumber", description="Purchase order number."
    )
    terms_of_sale: str | None = Field(default=None, alias="termsOfSale", description="Terms of sale.")
    exporter_tax_id: str | None = Field(default=None, alias="exporterTaxId", description="Exporter tax id.")
    consignee_tax_id: str | None = Field(default=None, alias="consigneeTaxId", description="Consignee tax id.")
    total_costs: ExportTotalCostsInput | None = Field(default=None, alias="totalCosts", description="Total costs.")
    sold_to: SoldToDetailsInput | None = Field(default=None, alias="soldTo", description="Sold to.")
    usps_specific: USPSSpecificInput | None = Field(default=None, alias="uspsSpecific", description="Usps specific.")
    fed_ex_specific: FedExSpecificInput | None = Field(
        default=None, alias="fedExSpecific", description="Fed ex specific."
    )
    ups_specific: UPSSpecificInput | None = Field(default=None, alias="upsSpecific", description="Ups specific.")


class ExpressFreightDetailInput(PackingRequestModel):
    """ExpressFreightDetail request contract (8_01)."""

    booking_confirmation_number: str | None = Field(
        default=None, alias="bookingConfirmationNumber", description="Booking confirmation number."
    )
    shippers_load_and_count: int = Field(
        default=0, alias="shippersLoadAndCount", description="Shippers load and count."
    )
    packing_list_enclosed: bool = Field(
        default=False, alias="packingListEnclosed", description="Packing list enclosed."
    )


class BookShipmentSpecificParamsInput(PackingRequestModel):
    """BookShipmentSpecificParams request contract (8_01)."""

    label_type: Literal[0, 1, 2, 3, 4, 5] = Field(default=0, alias="labelType", description="Label type.")
    payment_type: Literal[0, 1, 2] = Field(default=0, alias="paymentType", description="Payment type.")
    third_party_company_id: UUID | None = Field(
        default=None, alias="thirdPartyCompanyId", description="Third party company id."
    )
    label_image_type: Literal[0, 1, 2] = Field(default=0, alias="labelImageType", description="Label image type.")
    ready_hour: int = Field(default=0, alias="readyHour", description="Ready hour.", ge=0, le=24)
    fed_ex_express_freight_detail: ExpressFreightDetailInput | None = Field(
        default=None, alias="fedExExpressFreightDetail", description="Fed ex express freight detail."
    )


class BookShipmentRequestV2(PackingRequestModel):
    """BookShipmentRequestModelV2 request contract (8_01)."""

    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )
    force_update: bool = Field(
        default=False,
        alias="forceUpdate",
        description="Allow an overwrite-policy conflict override; refresh-policy conflicts still require a fresh read.",
    )
    quote_id: UUID = Field(
        alias="quoteId",
        description="Quote UUID from a shipping record or selected transportation quote; never a shipping ID.",
    )
    ship_out_date: datetime = Field(
        default=datetime.min,
        alias="shipOutDate",
        description="Requested shipment date and time; required by non-UPS carriers.",
    )
    international_params: JobExportDataInput | None = Field(
        default=None, alias="internationalParams", description="International params."
    )
    carrier_specific_params: BookShipmentSpecificParamsInput | None = Field(
        default=None, alias="carrierSpecificParams", description="Carrier specific params."
    )
    document_byte_code_required: bool = Field(
        default=False, alias="documentByteCodeRequired", description="Document byte code required."
    )
    handling_unit_freight_classes: list[str] | None = Field(
        default=None, alias="handlingUnitFreightClasses", description="Handling unit freight classes."
    )
    continue_on_validation_error: bool = Field(
        default=False, alias="continueOnValidationError", description="Continue on validation error."
    )

    @field_validator("quote_id")
    @classmethod
    def nonempty_quote(cls, value: UUID) -> UUID:
        """An empty GUID cannot identify a shipment quote."""
        if value.int == 0:
            raise ValueError("quote_id must identify a specific quote; the empty UUID is not valid")
        return value


class CancelShipmentRequest(PackingRequestModel):
    """CancelShipmentRequestModel request contract (8_01)."""

    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )
    force_update: bool = Field(
        default=False,
        alias="forceUpdate",
        description="Allow an overwrite-policy conflict override; refresh-policy conflicts still require a fresh read.",
    )
    force_delete: bool = Field(
        default=False, alias="forceDelete", description="Force cancellation only when explicitly requested."
    )


class FreightRateRequestAddressDetailsInput(PackingRequestModel):
    """FreightRateRequestAddressDetails request contract (8_01)."""

    address_line1: str | None = Field(default=None, alias="addressLine1", description="Address line1.")
    address_line2: str | None = Field(default=None, alias="addressLine2", description="Address line2.")
    city: str | None = Field(default=None, alias="city", description="City.")
    state: str | None = Field(default=None, alias="state", description="State.")
    zip_code: str | None = Field(default=None, alias="zipCode", description="Zip code.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")
    country_iata_code: str | None = Field(default=None, alias="countryIATACode", description="Country iata code.")
    alpha3_code: str | None = Field(default=None, alias="alpha3Code", description="Alpha3 code.")
    county_name: str | None = Field(default=None, alias="countyName", description="County name.")
    is_metric_system: bool = Field(default=False, alias="isMetricSystem", description="Is metric system.")


class ShipmentContactDetailsInput(PackingRequestModel):
    """ShipmentContactDetails request contract (8_01)."""

    contact_name: str | None = Field(default=None, alias="contactName", description="Contact name.")
    company_name: str | None = Field(default=None, alias="companyName", description="Company name.")
    phone_number: str | None = Field(default=None, alias="phoneNumber", description="Phone number.")
    email_address: str | None = Field(default=None, alias="emailAddress", description="Email address.")
    tax_id: str | None = Field(default=None, alias="taxId", description="Tax id.")
    address: FreightRateRequestAddressDetailsInput | None = Field(default=None, alias="address", description="Address.")


class ShippingExportRequest(PackingRequestModel):
    """InternationalParams request contract (8_01)."""

    commodities: list[ExportDataCommodityInput] | None = Field(
        default=None, alias="commodities", description="Commodities."
    )
    packing_info: list[ExportPackingInfoInput] | None = Field(
        default=None, alias="packingInfo", description="Packing info."
    )
    customs_value: float = Field(alias="customsValue", description="Customs value.")
    invoice_number: str | None = Field(default=None, alias="invoiceNumber", description="Invoice number.")
    purchase_order_number: str | None = Field(
        default=None, alias="purchaseOrderNumber", description="Purchase order number."
    )
    terms_of_sale: str | None = Field(default=None, alias="termsOfSale", description="Terms of sale.")
    exporter_tax_id: str | None = Field(default=None, alias="exporterTaxId", description="Exporter tax id.")
    consignee_tax_id: str | None = Field(default=None, alias="consigneeTaxId", description="Consignee tax id.")
    total_costs: ExportTotalCostsInput | None = Field(default=None, alias="totalCosts", description="Total costs.")
    sold_to: SoldToDetailsInput | None = Field(default=None, alias="soldTo", description="Sold to.")
    usps_specific: USPSSpecificInput | None = Field(default=None, alias="uspsSpecific", description="Usps specific.")
    fed_ex_specific: FedExSpecificInput | None = Field(
        default=None, alias="fedExSpecific", description="Fed ex specific."
    )
    ups_specific: UPSSpecificInput | None = Field(default=None, alias="upsSpecific", description="Ups specific.")
    values_specified: bool | None = Field(default=None, alias="valuesSpecified", description="Values specified.")
    sold_to_contact_details: ShipmentContactDetailsInput | None = Field(
        default=None, alias="soldToContactDetails", description="Sold to contact details."
    )


class ExportDataCommodityResult(ResponseModel):
    """ExportDataCommodity response contract (8_01)."""

    description: str | None = Field(default=None, alias="description", description="Description.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    unit_price: float | None = Field(default=None, alias="unitPrice", description="Unit price.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")
    country_iata_code: str | None = Field(default=None, alias="countryIATACode", description="Country iata code.")
    quantity: float | None = Field(default=None, alias="quantity", description="Quantity.")
    unit_of_measure: str | None = Field(default=None, alias="unitOfMeasure", description="Unit of measure.")
    schedule_b_number: str | None = Field(default=None, alias="scheduleBNumber", description="Schedule b number.")
    eccn: str | None = Field(default=None, alias="eccn", description="Eccn.")
    export_license_code: str | None = Field(default=None, alias="exportLicenseCode", description="Export license code.")
    special_marks: str | None = Field(default=None, alias="specialMarks", description="Special marks.")
    item_value: float | None = Field(default=None, alias="itemValue", description="Item value.")
    job_item_id: UUID | None = Field(
        default=None,
        alias="jobItemId",
        description="Export commodity item UUID; retained on GET/edit/POST round trips.",
    )
    full_description: str | None = Field(default=None, alias="fullDescription", description="Full description.")


class ExportPackingInfoResult(ResponseModel):
    """ExportPackingInfo response contract (8_01)."""

    commodity: int | None = Field(default=None, alias="commodity", description="Commodity.")
    package: str | None = Field(default=None, alias="package", description="Package.")
    package_number: int | None = Field(default=None, alias="packageNumber", description="Package number.")
    amount_in_package: int | None = Field(default=None, alias="amountInPackage", description="Amount in package.")


class ExportTotalCostsResult(ResponseModel):
    """ExportTotalCosts response contract (8_01)."""

    discount: float | None = Field(default=None, alias="discount", description="Discount.")
    insurance: float | None = Field(default=None, alias="insurance", description="Insurance.")
    freight: float | None = Field(default=None, alias="freight", description="Freight.")
    packing: float | None = Field(default=None, alias="packing", description="Packing.")
    handling: float | None = Field(default=None, alias="handling", description="Handling.")
    other: float | None = Field(default=None, alias="other", description="Other.")


class SoldToAddressResult(ResponseModel):
    """SoldToAddress response contract (8_01)."""

    address_line1: str | None = Field(default=None, alias="addressLine1", description="Address line1.")
    address_line2: str | None = Field(default=None, alias="addressLine2", description="Address line2.")
    city: str | None = Field(default=None, alias="city", description="City.")
    state: str | None = Field(default=None, alias="state", description="State.")
    zip_code: str | None = Field(default=None, alias="zipCode", description="Zip code.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")


class SoldToDetailsResult(ResponseModel):
    """SoldToDetails response contract (8_01)."""

    contact_name: str | None = Field(default=None, alias="contactName", description="Contact name.")
    company_name: str | None = Field(default=None, alias="companyName", description="Company name.")
    phone_number: str | None = Field(default=None, alias="phoneNumber", description="Phone number.")
    email_address: str | None = Field(default=None, alias="emailAddress", description="Email address.")
    address: SoldToAddressResult | None = Field(default=None, alias="address", description="Address.")
    tax_id: str | None = Field(default=None, alias="taxId", description="Tax id.")


class USPSSpecificResult(ResponseModel):
    """USPSSpecific response contract (8_01)."""

    aesitn: str | None = Field(default=None, alias="aesitn", description="Aesitn.")
    content_comments: str | None = Field(default=None, alias="contentComments", description="Content comments.")
    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")


class FedExSpecificResult(ResponseModel):
    """FedExSpecific response contract (8_01)."""

    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")
    special_instructions: str | None = Field(
        default=None, alias="specialInstructions", description="Special instructions."
    )
    payment_type: str | None = Field(default=None, alias="paymentType", description="Payment type.")
    export_compliance_statement: str | None = Field(
        default=None, alias="exportComplianceStatement", description="Export compliance statement."
    )


class UPSSpecificResult(ResponseModel):
    """UPSSpecific response contract (8_01)."""

    reason_for_export: str | None = Field(default=None, alias="reasonForExport", description="Reason for export.")
    shipper_memo: str | None = Field(default=None, alias="shipperMemo", description="Shipper memo.")
    invoice_date: datetime | None = Field(default=None, alias="invoiceDate", description="Invoice date.")
    duties_paid_by_sender: bool | None = Field(
        default=None, alias="dutiesPaidBySender", description="Duties paid by sender."
    )
    description_on_label: str | None = Field(
        default=None, alias="descriptionOnLabel", description="Description on label."
    )
    exemption_or_itn: str | None = Field(default=None, alias="exemptionOrITN", description="Exemption or itn.")


class FreightRateRequestAddressDetailsResult(ResponseModel):
    """FreightRateRequestAddressDetails response contract (8_01)."""

    address_line1: str | None = Field(default=None, alias="addressLine1", description="Address line1.")
    address_line2: str | None = Field(default=None, alias="addressLine2", description="Address line2.")
    city: str | None = Field(default=None, alias="city", description="City.")
    state: str | None = Field(default=None, alias="state", description="State.")
    zip_code: str | None = Field(default=None, alias="zipCode", description="Zip code.")
    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")
    country_iata_code: str | None = Field(default=None, alias="countryIATACode", description="Country iata code.")
    alpha3_code: str | None = Field(default=None, alias="alpha3Code", description="Alpha3 code.")
    county_name: str | None = Field(default=None, alias="countyName", description="County name.")
    is_metric_system: bool | None = Field(default=None, alias="isMetricSystem", description="Is metric system.")
    is_empty: bool | None = Field(default=None, alias="isEmpty", description="Is empty.")


class ShipmentContactDetailsResult(ResponseModel):
    """ShipmentContactDetails response contract (8_01)."""

    contact_name: str | None = Field(default=None, alias="contactName", description="Contact name.")
    company_name: str | None = Field(default=None, alias="companyName", description="Company name.")
    phone_number: str | None = Field(default=None, alias="phoneNumber", description="Phone number.")
    email_address: str | None = Field(default=None, alias="emailAddress", description="Email address.")
    tax_id: str | None = Field(default=None, alias="taxId", description="Tax id.")
    address: FreightRateRequestAddressDetailsResult | None = Field(
        default=None, alias="address", description="Address."
    )
    is_empty: bool | None = Field(default=None, alias="isEmpty", description="Is empty.")


class ShippingExportData(ResponseModel):
    """InternationalParams response contract (8_01)."""

    commodities: list[ExportDataCommodityResult] | None = Field(
        default=None, alias="commodities", description="Commodities."
    )
    packing_info: list[ExportPackingInfoResult] | None = Field(
        default=None, alias="packingInfo", description="Packing info."
    )
    customs_value: float | None = Field(default=None, alias="customsValue", description="Customs value.")
    invoice_number: str | None = Field(default=None, alias="invoiceNumber", description="Invoice number.")
    purchase_order_number: str | None = Field(
        default=None, alias="purchaseOrderNumber", description="Purchase order number."
    )
    terms_of_sale: str | None = Field(default=None, alias="termsOfSale", description="Terms of sale.")
    exporter_tax_id: str | None = Field(default=None, alias="exporterTaxId", description="Exporter tax id.")
    consignee_tax_id: str | None = Field(default=None, alias="consigneeTaxId", description="Consignee tax id.")
    total_costs: ExportTotalCostsResult | None = Field(default=None, alias="totalCosts", description="Total costs.")
    sold_to: SoldToDetailsResult | None = Field(default=None, alias="soldTo", description="Sold to.")
    usps_specific: USPSSpecificResult | None = Field(default=None, alias="uspsSpecific", description="Usps specific.")
    fed_ex_specific: FedExSpecificResult | None = Field(
        default=None, alias="fedExSpecific", description="Fed ex specific."
    )
    ups_specific: UPSSpecificResult | None = Field(default=None, alias="upsSpecific", description="Ups specific.")
    values_specified: bool | None = Field(default=None, alias="valuesSpecified", description="Values specified.")
    sold_to_contact_details: ShipmentContactDetailsResult | None = Field(
        default=None, alias="soldToContactDetails", description="Sold to contact details."
    )

    def to_request(self) -> ShippingExportRequest:
        """Prepare an edit/save body, excluding the computed ``fullDescription``.

        Commodity IDs and explicit nulls are preserved. Unknown server fields
        fail validation rather than disappearing from a replacement write.
        """
        payload = self.model_dump(by_alias=True, exclude_unset=True, mode="json")
        for commodity in payload.get("commodities") or []:
            commodity.pop("fullDescription", None)
        return ShippingExportRequest.model_validate(payload)


class ShipmentBookingResult(ResponseModel):
    """BookShipmentResponseModel response contract (8_01)."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    shipment_id: str | None = Field(
        default=None,
        alias="shipmentId",
        description="Carrier shipment identifier; distinct from Shipping.id and quoteId.",
    )
    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )


class ErrorResponseResult(ResponseModel):
    """ErrorResponse response contract (8_01)."""

    message: str | None = Field(default=None, alias="message", description="Message.")
    code: str | None = Field(default=None, alias="code", description="Code.")


class BookingValidationResult(ResponseModel):
    """BookingValidationResponse response contract (8_01)."""

    valid: bool | None = Field(default=None, alias="valid", description="Valid.")
    errors: list[ErrorResponseResult] | None = Field(default=None, alias="errors", description="Errors.")
    error: ErrorResponseResult | None = Field(default=None, alias="error", description="Error.")


class ShipmentCancelResult(ResponseModel):
    """DeleteShipmentResponse response contract (8_01)."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )
    override_error: bool | None = Field(default=None, alias="overrideError", description="Override error.")


class JobServiceAddOnModelInput(PackingRequestModel):
    """JobServiceAddOnModel request contract (8_01)."""

    carrier_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="carrierAPI", description="Carrier api."
    )
    unique_id: UUID = Field(default=UUID(int=0), alias="uniqueId", description="Unique id.")
    params: str | None = Field(default=None, alias="params", description="Params.")


class TransportationHandlingUnitModelInput(PackingRequestModel):
    """TransportationHandlingUnitModel request contract (8_01)."""

    id: int = Field(default=0, alias="id", description="Id.")
    quantity: int = Field(alias="quantity", description="Quantity.", ge=1, le=1000000)
    length: float | None = Field(default=None, alias="length", description="Length.", ge=0, le=1000)
    width: float | None = Field(default=None, alias="width", description="Width.", ge=0, le=1000)
    height: float | None = Field(default=None, alias="height", description="Height.", ge=0, le=1000)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=300000)
    declared_value: float | None = Field(
        default=None, alias="declaredValue", description="Declared value.", ge=0, le=1000000
    )
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    bol_description: str | None = Field(
        default=None, alias="bolDescription", description="Bol description.", max_length=250
    )
    freight_item_class: str | None = Field(
        default=None, alias="freightItemClass", description="Freight item class.", max_length=50
    )
    nmfc_item_no: str | None = Field(default=None, alias="nmfcItemNo", description="Nmfc item no.", max_length=50)


class RateRequestAddressModelInput(PackingRequestModel):
    """RateRequestAddressModel request contract (8_01)."""

    country_id: UUID | None = Field(default=None, alias="countryId", description="Country id.")
    zip_code: str = Field(alias="zipCode", description="Zip code.", min_length=1)
    address_line: str | None = Field(default=None, alias="addressLine", description="Address line.")
    country_iata_code: str | None = Field(default=None, alias="countryIATACode", description="Country iata code.")


class HandlingUnitRateRequest(PackingRequestModel):
    """RateRequestModel request contract (8_01)."""

    ship_out_date: datetime = Field(
        default=datetime.min,
        alias="shipOutDate",
        description="Requested shipment date and time; required by non-UPS carriers.",
    )
    transportation_add_ons: list[JobServiceAddOnModelInput] | None = Field(
        default=None, alias="transportationAddOns", description="Transportation add ons."
    )
    rate_sources: list[Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20]] | None = Field(
        default=None, alias="rateSources", description="Rate sources."
    )
    handling_units: list[TransportationHandlingUnitModelInput] = Field(
        alias="handlingUnits", description="Handling units included in this rate request.", min_length=1
    )
    origin_address: RateRequestAddressModelInput = Field(alias="originAddress", description="Origin address.")
    destination_address: RateRequestAddressModelInput = Field(
        alias="destinationAddress", description="Destination address."
    )
    skip_cache: bool = Field(default=False, alias="skipCache", description="Skip cache.")


class SelectQuoteRequest(PackingRequestModel):
    """SetRateModel request contract (8_01)."""

    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )
    force_update: bool = Field(
        default=False,
        alias="forceUpdate",
        description="Allow an overwrite-policy conflict override; refresh-policy conflicts still require a fresh read.",
    )
    rates_key: str = Field(
        alias="ratesKey",
        description="Opaque key returned by the rate request; required when selecting a quote.",
        min_length=1,
    )
    carrier_code: str = Field(
        alias="carrierCode",
        description="Carrier code from the chosen provider in the matching rate response.",
        min_length=1,
    )
    carrier_account_id: int | None = Field(default=None, alias="carrierAccountId", description="Carrier account id.")
    active: bool | None = Field(default=None, alias="active", description="Active.")
    pickup_agent_id: UUID | None = Field(default=None, alias="pickupAgentId", description="Pickup agent id.")


class CarrierAccessorialsResult(ResponseModel):
    """CarrierAccessorials response contract (8_01)."""

    service_category_id: UUID | None = Field(
        default=None, alias="serviceCategoryId", description="Service category id."
    )
    line_number: int | None = Field(default=None, alias="lineNumber", description="Line number.")
    service_description: str | None = Field(
        default=None, alias="serviceDescription", description="Service description."
    )
    charge_amount: float | None = Field(default=None, alias="chargeAmount", description="Charge amount.")
    markup_percent: float | None = Field(default=None, alias="markupPercent", description="Markup percent.")


class CarrierAccountInfoResult(ResponseModel):
    """CarrierAccountInfo response contract (8_01)."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    key: str | None = Field(default=None, alias="key", description="Key.")
    friendly_name: str | None = Field(default=None, alias="friendlyName", description="Friendly name.")


class ServiceAmountResult(ResponseModel):
    """ServiceAmount response contract (8_01)."""

    service_description: str | None = Field(
        default=None, alias="serviceDescription", description="Service description."
    )
    charge_amount: float | None = Field(default=None, alias="chargeAmount", description="Charge amount.")


class CarrierProviderResult(ResponseModel):
    """CarrierProvider response contract (8_01)."""

    quote_number: str | None = Field(default=None, alias="quoteNumber", description="Quote number.")
    carrier_name: str | None = Field(default=None, alias="carrierName", description="Carrier name.")
    carrier_code: str | None = Field(
        default=None,
        alias="carrierCode",
        description="Carrier code from the chosen provider in the matching rate response.",
    )
    fuel_charge_amount: float | None = Field(default=None, alias="fuelChargeAmount", description="Fuel charge amount.")
    net_amount: float | None = Field(default=None, alias="netAmount", description="Net amount.")
    caf_note: str | None = Field(default=None, alias="cafNote", description="Caf note.")
    service_days: int | None = Field(default=None, alias="serviceDays", description="Service days.")
    service_days_asterisk: bool | None = Field(
        default=None, alias="serviceDaysAsterisk", description="Service days asterisk."
    )
    estimated_arrival: datetime | None = Field(default=None, alias="estimatedArrival", description="Estimated arrival.")
    custom_message: str | None = Field(default=None, alias="customMessage", description="Custom message.")
    accessorials: list[CarrierAccessorialsResult] | None = Field(
        default=None, alias="accessorials", description="Accessorials."
    )
    total_services_cost: float | None = Field(
        default=None, alias="totalServicesCost", description="Total services cost."
    )
    total_without_service: float | None = Field(
        default=None, alias="totalWithoutService", description="Total without service."
    )
    freight_sell: float | None = Field(default=None, alias="freightSell", description="Freight sell.")
    accessorial_sell: float | None = Field(default=None, alias="accessorialSell", description="Accessorial sell.")
    total_sell: float | None = Field(default=None, alias="totalSell", description="Total sell.")
    source_id: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="sourceId", description="Source id."
    )
    used_carrier_account_info: CarrierAccountInfoResult | None = Field(
        default=None, alias="usedCarrierAccountInfo", description="Used carrier account info."
    )
    net_breakdown: list[ServiceAmountResult] | None = Field(
        default=None, alias="netBreakdown", description="Net breakdown."
    )


class CarrierProviderMessageResult(ResponseModel):
    """CarrierProviderMessage response contract (8_01)."""

    source_id: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="sourceId", description="Source id."
    )
    message: str | None = Field(default=None, alias="message", description="Message.")


class ObtainNFMHandlingUnitResult(ResponseModel):
    """ObtainNFMHandlingUnit response contract (8_01)."""

    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    declared_value: float | None = Field(default=None, alias="declaredValue", description="Declared value.")
    freight_item_class: str | None = Field(default=None, alias="freightItemClass", description="Freight item class.")


class NameValueEntityResult(ResponseModel):
    """NameValueEntity response contract (8_01)."""

    name: str | None = Field(default=None, alias="name", description="Name.")
    value: str | None = Field(default=None, alias="value", description="Value.")


class ObtainNFMTransportationAddOnResult(ResponseModel):
    """ObtainNFMTransportationAddOn response contract (8_01)."""

    carrier_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="carrierAPI", description="Carrier api."
    )
    unique_id: UUID | None = Field(default=None, alias="uniqueId", description="Unique id.")
    params: list[NameValueEntityResult] | None = Field(default=None, alias="params", description="Params.")


class RateRequestSnapshotResult(ResponseModel):
    """RateRequestSnapshot response contract (8_01)."""

    from_zip: str | None = Field(default=None, alias="fromZip", description="From zip.")
    to_zip: str | None = Field(default=None, alias="toZip", description="To zip.")
    handling_units: list[ObtainNFMHandlingUnitResult] | None = Field(
        default=None, alias="handlingUnits", description="Handling units included in this rate request."
    )
    transportation_add_ons: list[ObtainNFMTransportationAddOnResult] | None = Field(
        default=None, alias="transportationAddOns", description="Transportation add ons."
    )
    ship_out_date: datetime | None = Field(
        default=None, alias="shipOutDate", description="Requested shipment date and time; required by non-UPS carriers."
    )


class HandlingUnitRates(ResponseModel):
    """KeyedRatesResponse response contract (8_01)."""

    providers: list[CarrierProviderResult] | None = Field(default=None, alias="providers", description="Providers.")
    errors: list[CarrierProviderMessageResult] | None = Field(default=None, alias="errors", description="Errors.")
    warnings: list[CarrierProviderMessageResult] | None = Field(default=None, alias="warnings", description="Warnings.")
    filtration_messages: list[CarrierProviderMessageResult] | None = Field(
        default=None, alias="filtrationMessages", description="Filtration messages."
    )
    rates_key: str | None = Field(
        default=None,
        alias="ratesKey",
        description="Opaque key returned by the rate request; required when selecting a quote.",
    )
    request_snapshot: RateRequestSnapshotResult | None = Field(
        default=None, alias="requestSnapshot", description="Request snapshot."
    )


class TransportationQuoteResult(ResponseModel):
    """TransportationQuote response contract (8_01)."""

    id: UUID | None = Field(default=None, alias="id", description="Id.")
    active: bool | None = Field(default=None, alias="active", description="Active.")
    shipment_type: UUID | None = Field(default=None, alias="shipmentType", description="Shipment type.")
    provider_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="providerAPI", description="Provider api."
    )
    provider_id: UUID | None = Field(default=None, alias="providerId", description="Provider id.")
    provider_code: str | None = Field(default=None, alias="providerCode", description="Provider code.")
    provider_company_name: str | None = Field(
        default=None, alias="providerCompanyName", description="Provider company name."
    )
    freight_amount: float | None = Field(default=None, alias="freightAmount", description="Freight amount.")
    accessorial_amount: float | None = Field(default=None, alias="accessorialAmount", description="Accessorial amount.")
    bill_to_franchisee_id: UUID | None = Field(
        default=None, alias="billToFranchiseeId", description="Bill to franchisee id."
    )
    bill_to_franchisee_code: str | None = Field(
        default=None, alias="billToFranchiseeCode", description="Bill to franchisee code."
    )
    service_days: int | None = Field(default=None, alias="serviceDays", description="Service days.")
    quote_number: str | None = Field(default=None, alias="quoteNumber", description="Quote number.")
    estimated_arrival: datetime | None = Field(default=None, alias="estimatedArrival", description="Estimated arrival.")
    shipment_accepted: bool | None = Field(default=None, alias="shipmentAccepted", description="Shipment accepted.")
    shipment_accepted_date: datetime | None = Field(
        default=None, alias="shipmentAcceptedDate", description="Shipment accepted date."
    )
    pro_number: str | None = Field(default=None, alias="proNumber", description="Pro number.")
    is_overridden: bool | None = Field(default=None, alias="isOverridden", description="Is overridden.")
    used_carrier_account_info: CarrierAccountInfoResult | None = Field(
        default=None, alias="usedCarrierAccountInfo", description="Used carrier account info."
    )
    quote_snapshot: str | None = Field(default=None, alias="quoteSnapshot", description="Quote snapshot.")
    shipping_id: int | None = Field(
        default=None, alias="shippingId", description="Integer ID of the shipping record that owns this quote."
    )
    order_in_shipping: int | None = Field(default=None, alias="orderInShipping", description="Order in shipping.")
    created_by: int | None = Field(default=None, alias="createdBy", description="Created by.")
    created_date: datetime | None = Field(default=None, alias="createdDate", description="Created date.")
    modified_by: int | None = Field(default=None, alias="modifiedBy", description="Modified by.")
    modified_date: datetime | None = Field(default=None, alias="modifiedDate", description="Modified date.")


class SelectedQuoteResult(ResponseModel):
    """SaveRateQuoteResponse response contract (8_01)."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for optimistic concurrency.",
    )
    transportation_quote: TransportationQuoteResult | None = Field(
        default=None, alias="transportationQuote", description="Transportation quote."
    )
