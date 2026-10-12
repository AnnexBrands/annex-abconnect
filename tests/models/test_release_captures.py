"""Reviewed, sanitized staging fixtures for the 8_01 release."""

from ab.api.models import (
    BookingValidationResult,
    CarrierShipmentDetails,
    CommonInventory,
    EditableFormContent,
    HandlingUnitMaterial,
    HandlingUnitMaterialsResponseServiceResponseResult,
    HandlingUnitRates,
    JobHandlingUnit,
    JobHandlingUnitDetails,
    JobHandlingUnitListServiceResponseResult,
    JobInventoryItem,
    JobServiceAddOnResult,
    ManageHandlingUnitsResponse,
    MasterMaterialInfoResult,
    MaterialResult,
    SaveRateQuoteResponseResult,
    ServiceAddOnEntityResult,
    ShipmentBookingResult,
    ShipmentCancelResult,
    ShipmentFormPlan,
    Shipping,
    ShippingExportData,
    SuggestedCombinedHandlingUnitListServiceResponseResult,
    SuggestedHandlingUnitServiceResponseResult,
    SuggestedHierarchyHandlingUnitListServiceResponseResult,
    TransportationQuoteResult,
    ValidateHandlingUnitResultResult,
)
from tests.conftest import assert_no_extra_fields, require_fixture


def test_job_inventory_item_real_capture():
    data = require_fixture("JobInventoryItem", required=True)
    result = JobInventoryItem.model_validate(data)
    assert isinstance(result, JobInventoryItem)
    assert_no_extra_fields(result)


def test_job_handling_unit_real_capture():
    data = require_fixture("JobHandlingUnit", required=True)
    result = JobHandlingUnit.model_validate(data)
    assert isinstance(result, JobHandlingUnit)
    assert_no_extra_fields(result)


def test_job_handling_unit_details_real_capture():
    data = require_fixture("JobHandlingUnitDetails", required=True)
    result = JobHandlingUnitDetails.model_validate(data)
    assert isinstance(result, JobHandlingUnitDetails)
    assert_no_extra_fields(result)


def test_shipping_real_capture():
    data = require_fixture("Shipping", required=True)
    result = Shipping.model_validate(data)
    assert isinstance(result, Shipping)
    assert_no_extra_fields(result)


def test_shipping_export_data_real_capture():
    data = require_fixture("ShippingExportData", required=True)
    result = ShippingExportData.model_validate(data)
    assert isinstance(result, ShippingExportData)
    assert_no_extra_fields(result)


def test_common_inventory_real_capture():
    data = require_fixture("CommonInventory", required=True)
    result = CommonInventory.model_validate(data)
    assert isinstance(result, CommonInventory)
    assert_no_extra_fields(result)


def test_master_material_info_result_real_capture():
    data = require_fixture("MasterMaterialInfoResult", required=True)
    assert isinstance(data, list)
    for row in data:
        result = MasterMaterialInfoResult.model_validate(row)
        assert isinstance(result, MasterMaterialInfoResult)
        assert_no_extra_fields(result)


def test_material_result_real_capture():
    data = require_fixture("MaterialResult", required=True)
    assert isinstance(data, list)
    for row in data:
        result = MaterialResult.model_validate(row)
        assert isinstance(result, MaterialResult)
        assert_no_extra_fields(result)


def test_service_add_on_entity_result_real_capture():
    data = require_fixture("ServiceAddOnEntityResult", required=True)
    assert isinstance(data, list)
    for row in data:
        result = ServiceAddOnEntityResult.model_validate(row)
        assert isinstance(result, ServiceAddOnEntityResult)
        assert_no_extra_fields(result)


def test_job_service_add_on_result_real_capture():
    data = require_fixture("JobServiceAddOnResult", required=True)
    assert isinstance(data, list)
    for row in data:
        result = JobServiceAddOnResult.model_validate(row)
        assert isinstance(result, JobServiceAddOnResult)
        assert_no_extra_fields(result)


def test_handling_unit_material_real_capture():
    data = require_fixture("HandlingUnitMaterial", required=True)
    assert isinstance(data, list)
    for row in data:
        result = HandlingUnitMaterial.model_validate(row)
        assert isinstance(result, HandlingUnitMaterial)
        assert_no_extra_fields(result)


def test_transportation_quote_result_real_capture():
    data = require_fixture("TransportationQuoteResult", required=True)
    assert isinstance(data, list)
    for row in data:
        result = TransportationQuoteResult.model_validate(row)
        assert isinstance(result, TransportationQuoteResult)
        assert_no_extra_fields(result)


def test_booking_validation_result_real_capture():
    data = require_fixture("BookingValidationResult", required=True)
    result = BookingValidationResult.model_validate(data)
    assert isinstance(result, BookingValidationResult)
    assert_no_extra_fields(result)


def test_shipment_form_plan_real_capture():
    data = require_fixture("ShipmentFormPlan", required=True)
    assert isinstance(data, list)
    for row in data:
        result = ShipmentFormPlan.model_validate(row)
        assert isinstance(result, ShipmentFormPlan)
        assert_no_extra_fields(result)


def test_suggested_combined_handling_unit_list_service_response_result_real_capture():
    data = require_fixture("SuggestedCombinedHandlingUnitListServiceResponseResult", required=True)
    result = SuggestedCombinedHandlingUnitListServiceResponseResult.model_validate(data)
    assert isinstance(result, SuggestedCombinedHandlingUnitListServiceResponseResult)
    assert_no_extra_fields(result)


def test_suggested_handling_unit_service_response_result_real_capture():
    data = require_fixture("SuggestedHandlingUnitServiceResponseResult", required=True)
    result = SuggestedHandlingUnitServiceResponseResult.model_validate(data)
    assert isinstance(result, SuggestedHandlingUnitServiceResponseResult)
    assert_no_extra_fields(result)


def test_suggested_hierarchy_handling_unit_list_service_response_result_real_capture():
    data = require_fixture("SuggestedHierarchyHandlingUnitListServiceResponseResult", required=True)
    result = SuggestedHierarchyHandlingUnitListServiceResponseResult.model_validate(data)
    assert isinstance(result, SuggestedHierarchyHandlingUnitListServiceResponseResult)
    assert_no_extra_fields(result)


def test_validate_handling_unit_result_result_real_capture():
    data = require_fixture("ValidateHandlingUnitResultResult", required=True)
    result = ValidateHandlingUnitResultResult.model_validate(data)
    assert isinstance(result, ValidateHandlingUnitResultResult)
    assert_no_extra_fields(result)


def test_handling_unit_materials_response_service_response_result_real_capture():
    data = require_fixture("HandlingUnitMaterialsResponseServiceResponseResult", required=True)
    result = HandlingUnitMaterialsResponseServiceResponseResult.model_validate(data)
    assert isinstance(result, HandlingUnitMaterialsResponseServiceResponseResult)
    assert_no_extra_fields(result)


def test_job_handling_unit_list_service_response_result_real_capture():
    data = require_fixture("JobHandlingUnitListServiceResponseResult", required=True)
    result = JobHandlingUnitListServiceResponseResult.model_validate(data)
    assert isinstance(result, JobHandlingUnitListServiceResponseResult)
    assert_no_extra_fields(result)


def test_manage_handling_units_response_real_capture():
    data = require_fixture("ManageHandlingUnitsResponse", required=True)
    result = ManageHandlingUnitsResponse.model_validate(data)
    assert isinstance(result, ManageHandlingUnitsResponse)
    assert_no_extra_fields(result)


def test_editable_form_content_real_capture():
    data = require_fixture("EditableFormContent", required=True)
    result = EditableFormContent.model_validate(data)
    assert isinstance(result, EditableFormContent)
    assert_no_extra_fields(result)


def test_carrier_shipment_details_real_capture():
    data = require_fixture("CarrierShipmentDetails", required=True)
    result = CarrierShipmentDetails.model_validate(data)
    assert isinstance(result, CarrierShipmentDetails)
    assert_no_extra_fields(result)


def test_shipment_cancel_result_real_capture():
    data = require_fixture("ShipmentCancelResult", required=True)
    result = ShipmentCancelResult.model_validate(data)
    assert isinstance(result, ShipmentCancelResult)
    assert_no_extra_fields(result)


def test_handling_unit_rates_real_capture():
    data = require_fixture("HandlingUnitRates", required=True)
    result = HandlingUnitRates.model_validate(data)
    assert isinstance(result, HandlingUnitRates)
    assert_no_extra_fields(result)


def test_save_rate_quote_response_result_real_capture():
    data = require_fixture("SaveRateQuoteResponseResult", required=True)
    result = SaveRateQuoteResponseResult.model_validate(data)
    assert isinstance(result, SaveRateQuoteResponseResult)
    assert_no_extra_fields(result)


def test_shipment_booking_result_real_capture():
    data = require_fixture("ShipmentBookingResult", required=True)
    result = ShipmentBookingResult.model_validate(data)
    assert isinstance(result, ShipmentBookingResult)
    assert_no_extra_fields(result)
