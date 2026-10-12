"""Additional typed 8_01 packing, quote, and tracking contracts.

Derived from the bundled schema and reconciled against release controllers.
Requests reject unknown nested fields; responses preserve server additions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel
from ab.api.models.packing import PackingRequestModel
from ab.api.models.transportation import CarrierAccountInfoResult, TransportationQuoteResult


class CommonInventory(ResponseModel):
    """CommonInventoryItem response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    company_id: UUID | None = Field(default=None, alias="companyId", description="Company id.")
    is_active: bool | None = Field(default=None, alias="isActive", description="Is active.")
    is_public: bool | None = Field(default=None, alias="isPublic", description="Is public.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    value: float | None = Field(default=None, alias="value", description="Value.")
    c_pack_id: UUID | None = Field(default=None, alias="cPackId", description="C pack id.")
    eccn: str | None = Field(default=None, alias="eccn", description="Eccn.")
    schedule_b: str | None = Field(default=None, alias="scheduleB", description="Schedule b.")
    parent_inventory_item_id: int | None = Field(
        default=None, alias="parentInventoryItemId", description="Parent inventory item id."
    )


class CommonInventoryRequest(PackingRequestModel):
    """CommonInventoryItemModel request contract from 8_01."""

    name: str | None = Field(default=None, alias="name", description="Name.", max_length=250)
    is_active: bool = Field(alias="isActive", description="Is active.")
    is_public: bool = Field(alias="isPublic", description="Is public.")
    length: float | None = Field(default=None, alias="length", description="Length.", ge=0, le=1000)
    width: float | None = Field(default=None, alias="width", description="Width.", ge=0, le=1000)
    height: float | None = Field(default=None, alias="height", description="Height.", ge=0, le=1000)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=300000)
    value: float | None = Field(default=None, alias="value", description="Value.", ge=0, le=1000000)
    c_pack_id: UUID | None = Field(default=None, alias="cPackId", description="C pack id.")
    eccn: str | None = Field(default=None, alias="eccn", description="Eccn.", max_length=16)
    schedule_b: str | None = Field(default=None, alias="scheduleB", description="Schedule b.", max_length=16)
    parent_inventory_item_id: int | None = Field(
        default=None, alias="parentInventoryItemId", description="Parent inventory item id."
    )


class MasterMaterialInfoResult(ResponseModel):
    """MasterMaterialInfo response contract from 8_01."""

    material_id: UUID | None = Field(default=None, alias="materialID", description="Material id.")
    material_name: str | None = Field(default=None, alias="materialName", description="Material name.")
    material_description: str | None = Field(
        default=None, alias="materialDescription", description="Material description."
    )
    unit_cost: float | None = Field(default=None, alias="unitCost", description="Unit cost.")
    nc_material_id: int | None = Field(default=None, alias="ncMaterialId", description="Nc material id.")


class MaterialResult(ResponseModel):
    """Material response contract from 8_01."""

    material_id: int | None = Field(default=None, alias="materialID", description="Material id.")
    company_id: UUID | None = Field(default=None, alias="companyId", description="Company id.")
    code: str | None = Field(default=None, alias="code", description="Code.")
    type: str | None = Field(default=None, alias="type", description="Type.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    description: str | None = Field(default=None, alias="description", description="Description.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    cost: float | None = Field(default=None, alias="cost", description="Cost.")
    price: float | None = Field(default=None, alias="price", description="Price.")
    waste_factor: float | None = Field(default=None, alias="wasteFactor", description="Waste factor.")
    default_fill: float | None = Field(default=None, alias="defaultFill", description="Default fill.")


class PackInventoryItemModelInput(PackingRequestModel):
    """PackInventoryItemModel request contract from 8_01."""

    c_pack_name: str = Field(alias="cPackName", description="C pack name.", min_length=1)
    sequence_no: int = Field(alias="sequenceNo", description="Sequence no.", ge=1, le=1000)
    length: float | None = Field(default=None, alias="length", description="Length.", ge=0, le=9999)
    width: float | None = Field(default=None, alias="width", description="Width.", ge=0, le=9999)
    height: float | None = Field(default=None, alias="height", description="Height.", ge=0, le=9999)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=999999)
    value: float | None = Field(default=None, alias="value", description="Value.", ge=0, le=9999999.99)
    name: str | None = Field(default=None, alias="name", description="Name.", max_length=250)
    quantity: int = Field(alias="quantity", description="Quantity.", ge=1, le=9999999)


class PendingHandlingUnitMaterialResult(ResponseModel):
    """PendingHandlingUnitMaterial response contract from 8_01."""

    material_id: int | None = Field(default=None, alias="materialId", description="Material id.")
    quantity_planned: float | None = Field(default=None, alias="quantityPlanned", description="Quantity planned.")
    unit_cost: float | None = Field(default=None, alias="unitCost", description="Unit cost.")
    waste_quantity: float | None = Field(default=None, alias="wasteQuantity", description="Waste quantity.")
    description: str | None = Field(default=None, alias="description", description="Description.")
    material_name: str | None = Field(default=None, alias="materialName", description="Material name.")
    material_weight: float | None = Field(default=None, alias="materialWeight", description="Material weight.")
    material_cost: float | None = Field(default=None, alias="materialCost", description="Material cost.")
    material_price: float | None = Field(default=None, alias="materialPrice", description="Material price.")


class SuggestedHandlingUnitResult(ResponseModel):
    """SuggestedHandlingUnit response contract from 8_01."""

    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    fill_rate: float | None = Field(default=None, alias="fillRate", description="Fill rate.")
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.")
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", description="Container thickness."
    )
    materials: list[PendingHandlingUnitMaterialResult] | None = Field(
        default=None, alias="materials", description="Materials."
    )
    material_total_cost: float | None = Field(
        default=None, alias="materialTotalCost", description="Material total cost."
    )
    fill_weight: float | None = Field(default=None, alias="fillWeight", description="Fill weight.")
    container_weight: float | None = Field(default=None, alias="containerWeight", description="Container weight.")
    material_weight: float | None = Field(default=None, alias="materialWeight", description="Material weight.")
    container_material_id: int | None = Field(
        default=None, alias="containerMaterialId", description="Container material id."
    )
    freight_class_id: UUID | None = Field(default=None, alias="freightClassId", description="Freight class id.")


class SuggestedHandlingUnitServiceResponseResult(ResponseModel):
    """SuggestedHandlingUnitServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: SuggestedHandlingUnitResult | None = Field(default=None, alias="data", description="Data.")


class AddContentHandlingUnitModelInput(PackingRequestModel):
    """AddContentHandlingUnitModel request contract from 8_01."""

    count: int | None = Field(default=None, alias="count", description="Count.", ge=0, le=9999999)
    id: int | None = Field(default=None, alias="id", description="Id.")


class PackHierarchyHandlingUnitModelInput(PackingRequestModel):
    """PackHierarchyHandlingUnitModel request contract from 8_01."""

    id: int = Field(alias="id", description="Id.")
    quantity: int = Field(alias="quantity", description="Quantity.", ge=1, le=9999999)
    sequence_no: int = Field(alias="sequenceNo", description="Sequence no.", ge=1, le=1000)
    length: float | None = Field(default=None, alias="length", description="Length.", ge=0, le=9999)
    width: float | None = Field(default=None, alias="width", description="Width.", ge=0, le=9999)
    height: float | None = Field(default=None, alias="height", description="Height.", ge=0, le=9999)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=999999)
    declared_value: float | None = Field(
        default=None, alias="declaredValue", description="Declared value.", ge=0, le=9999999.99
    )
    inventory_items: list[PackInventoryItemModelInput] = Field(alias="inventoryItems", description="Inventory items.")
    content_handling_units: list[AddContentHandlingUnitModelInput] = Field(
        alias="contentHandlingUnits", description="Content handling units."
    )


class PendingPackItemResult(ResponseModel):
    """PendingPackItem response contract from 8_01."""

    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    force_crate: bool | None = Field(default=None, alias="forceCrate", description="Force crate.")
    value: float | None = Field(default=None, alias="value", description="Value.")
    c_pack_name: str | None = Field(default=None, alias="cPackName", description="C pack name.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")


class ContentHandlingUnitResult(ResponseModel):
    """ContentHandlingUnit response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    count: int | None = Field(default=None, alias="count", description="Count.")


class SuggestedHierarchyHandlingUnitResult(ResponseModel):
    """SuggestedHierarchyHandlingUnit response contract from 8_01."""

    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    fill_rate: float | None = Field(default=None, alias="fillRate", description="Fill rate.")
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.")
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", description="Container thickness."
    )
    materials: list[PendingHandlingUnitMaterialResult] | None = Field(
        default=None, alias="materials", description="Materials."
    )
    material_total_cost: float | None = Field(
        default=None, alias="materialTotalCost", description="Material total cost."
    )
    fill_weight: float | None = Field(default=None, alias="fillWeight", description="Fill weight.")
    container_weight: float | None = Field(default=None, alias="containerWeight", description="Container weight.")
    material_weight: float | None = Field(default=None, alias="materialWeight", description="Material weight.")
    container_material_id: int | None = Field(
        default=None, alias="containerMaterialId", description="Container material id."
    )
    freight_class_id: UUID | None = Field(default=None, alias="freightClassId", description="Freight class id.")
    id: int | None = Field(default=None, alias="id", description="Id.")
    inventory_items: list[PendingPackItemResult] | None = Field(
        default=None, alias="inventoryItems", description="Inventory items."
    )
    content_handling_units: list[ContentHandlingUnitResult] | None = Field(
        default=None, alias="contentHandlingUnits", description="Content handling units."
    )


class SuggestedHierarchyHandlingUnitListServiceResponseResult(ResponseModel):
    """SuggestedHierarchyHandlingUnitListServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: list[SuggestedHierarchyHandlingUnitResult] | None = Field(default=None, alias="data", description="Data.")


class AddedPendingPackItemResult(ResponseModel):
    """AddedPendingPackItem response contract from 8_01."""

    item: PendingPackItemResult | None = Field(default=None, alias="item", description="Item.")
    count: int | None = Field(default=None, alias="count", description="Count.")


class SuggestedCombinedHandlingUnitResult(ResponseModel):
    """SuggestedCombinedHandlingUnit response contract from 8_01."""

    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    fill_rate: float | None = Field(default=None, alias="fillRate", description="Fill rate.")
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.")
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", description="Container thickness."
    )
    materials: list[PendingHandlingUnitMaterialResult] | None = Field(
        default=None, alias="materials", description="Materials."
    )
    material_total_cost: float | None = Field(
        default=None, alias="materialTotalCost", description="Material total cost."
    )
    fill_weight: float | None = Field(default=None, alias="fillWeight", description="Fill weight.")
    container_weight: float | None = Field(default=None, alias="containerWeight", description="Container weight.")
    material_weight: float | None = Field(default=None, alias="materialWeight", description="Material weight.")
    container_material_id: int | None = Field(
        default=None, alias="containerMaterialId", description="Container material id."
    )
    freight_class_id: UUID | None = Field(default=None, alias="freightClassId", description="Freight class id.")
    inventory_items: list[AddedPendingPackItemResult] | None = Field(
        default=None, alias="inventoryItems", description="Inventory items."
    )


class SuggestedCombinedHandlingUnitListServiceResponseResult(ResponseModel):
    """SuggestedCombinedHandlingUnitListServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: list[SuggestedCombinedHandlingUnitResult] | None = Field(default=None, alias="data", description="Data.")


class PackagingItemDataInput(PackingRequestModel):
    """PackagingItemData request contract from 8_01."""

    length: float = Field(alias="length", description="Length.", ge=0, le=9999)
    width: float = Field(alias="width", description="Width.", ge=0, le=9999)
    height: float = Field(alias="height", description="Height.", ge=0, le=9999)
    weight: float = Field(alias="weight", description="Weight.", ge=0, le=999999)
    value: float | None = Field(default=None, alias="value", description="Value.", ge=0, le=9999999.99)
    c_pack_id: UUID | None = Field(default=None, alias="cPackId", description="C pack id.")
    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.", ge=1, le=9999999)


class GetHandlingUnitMaterialsModelInput(PackingRequestModel):
    """GetHandlingUnitMaterialsModel request contract from 8_01."""

    c_pack_name: str = Field(alias="cPackName", description="C pack name.", min_length=1)
    container_type_id: int = Field(alias="containerTypeId", description="Container type id.")
    container_id: int | None = Field(default=None, alias="containerId", description="Container id.")
    length: float = Field(alias="length", description="Length.", ge=0, le=9999)
    width: float = Field(alias="width", description="Width.", ge=0, le=9999)
    height: float = Field(alias="height", description="Height.", ge=0, le=9999)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=999999)
    value: float | None = Field(default=None, alias="value", description="Value.", ge=0, le=9999999.99)
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.", ge=0, le=100)
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    fill_rate: float | None = Field(default=None, alias="fillRate", description="Fill rate.", ge=0, le=100)
    transportation_type: str | None = Field(
        default=None, alias="transportationType", description="Transportation type."
    )
    content_data: list[PackagingItemDataInput] | None = Field(
        default=None, alias="contentData", description="Content data."
    )


class ContainerInformationResult(ResponseModel):
    """ContainerInformation response contract from 8_01."""

    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")


class ValidateHandlingUnitBaseResultResult(ResponseModel):
    """ValidateHandlingUnitBaseResult response contract from 8_01."""

    container_valid: bool | None = Field(default=None, alias="containerValid", description="Container valid.")
    c_fill_valid: bool | None = Field(default=None, alias="cFillValid", description="C fill valid.")


class HandlingUnitMaterialsResponseResult(ResponseModel):
    """HandlingUnitMaterialsResponse response contract from 8_01."""

    container_information: ContainerInformationResult | None = Field(
        default=None, alias="containerInformation", description="Container information."
    )
    materials: list[PendingHandlingUnitMaterialResult] | None = Field(
        default=None, alias="materials", description="Materials."
    )
    validation_result: ValidateHandlingUnitBaseResultResult | None = Field(
        default=None, alias="validationResult", description="Validation result."
    )


class HandlingUnitMaterialsResponseServiceResponseResult(ResponseModel):
    """HandlingUnitMaterialsResponseServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: HandlingUnitMaterialsResponseResult | None = Field(default=None, alias="data", description="Data.")


class ContainerDimensionsInput(PackingRequestModel):
    """ContainerDimensions request contract from 8_01."""

    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")


class ValidateHandlingUnitModelInput(PackingRequestModel):
    """ValidateHandlingUnitModel request contract from 8_01."""

    inventory_items_model: list[PackInventoryItemModelInput] = Field(
        alias="inventoryItemsModel", description="Inventory items model."
    )
    container_type_id: int = Field(alias="containerTypeId", description="Container type id.")
    container_id: int | None = Field(default=None, alias="containerId", description="Container id.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    trans_type: str | None = Field(default=None, alias="transType", description="Trans type.")
    container_dimensions: ContainerDimensionsInput | None = Field(
        default=None, alias="containerDimensions", description="Container dimensions."
    )


class ValidateHandlingUnitResultResult(ResponseModel):
    """ValidateHandlingUnitResult response contract from 8_01."""

    container_valid: bool | None = Field(default=None, alias="containerValid", description="Container valid.")
    c_fill_valid: bool | None = Field(default=None, alias="cFillValid", description="C fill valid.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")

    fill: dict[str, Any] | None = Field(
        None, description="Optional staging validation metadata, absent from the release Swagger."
    )
    container_material: dict[str, Any] | None = Field(
        None,
        alias="containerMaterial",
        description="Optional staging container metadata; preserved without interpretation.",
    )


class HandlingUnitPackagingInformationInput(PackingRequestModel):
    """HandlingUnitPackagingInformation request contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.", ge=1, le=9999999)
    weight: float | None = Field(default=None, alias="weight", description="Weight.", ge=0, le=999999)
    length: float | None = Field(default=None, alias="length", description="Length.", ge=0, le=9999)
    width: float | None = Field(default=None, alias="width", description="Width.", ge=0, le=9999)
    height: float | None = Field(default=None, alias="height", description="Height.", ge=0, le=9999)
    declared_value: float | None = Field(default=None, alias="declaredValue", description="Declared value.")


class PackHandlingUnitsModelInput(PackingRequestModel):
    """PackHandlingUnitsModel request contract from 8_01."""

    handling_units: list[HandlingUnitPackagingInformationInput] = Field(
        alias="handlingUnits", description="Handling units."
    )
    requested_freight_packaging_code: str | None = Field(
        default=None, alias="requestedFreightPackagingCode", description="Requested freight packaging code."
    )


class ContentInventoryItemResult(ResponseModel):
    """ContentInventoryItem response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    count: int | None = Field(default=None, alias="count", description="Count.")


class HandlingUnitMaterialResult(ResponseModel):
    """HandlingUnitMaterial response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    material_id: int | None = Field(default=None, alias="materialId", description="Material id.")
    material_name: str | None = Field(default=None, alias="materialName", description="Material name.")
    material_description: str | None = Field(
        default=None, alias="materialDescription", description="Material description."
    )
    quantity_planned: float | None = Field(default=None, alias="quantityPlanned", description="Quantity planned.")
    unit_cost: float | None = Field(default=None, alias="unitCost", description="Unit cost.")
    added_by_auto_packer: bool | None = Field(
        default=None, alias="addedByAutoPacker", description="Added by auto packer."
    )
    waste_quantity: float | None = Field(default=None, alias="wasteQuantity", description="Waste quantity.")
    quantity: float | None = Field(default=None, alias="quantity", description="Quantity.")


class ContainerDimensionsResult(ResponseModel):
    """ContainerDimensions response contract from 8_01."""

    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")


class ContainerHandlingUnitMaterialResult(ResponseModel):
    """ContainerHandlingUnitMaterial response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    material_id: int | None = Field(default=None, alias="materialId", description="Material id.")
    material_name: str | None = Field(default=None, alias="materialName", description="Material name.")
    material_description: str | None = Field(
        default=None, alias="materialDescription", description="Material description."
    )
    quantity_planned: float | None = Field(default=None, alias="quantityPlanned", description="Quantity planned.")
    unit_cost: float | None = Field(default=None, alias="unitCost", description="Unit cost.")
    added_by_auto_packer: bool | None = Field(
        default=None, alias="addedByAutoPacker", description="Added by auto packer."
    )
    waste_quantity: float | None = Field(default=None, alias="wasteQuantity", description="Waste quantity.")
    quantity: float | None = Field(default=None, alias="quantity", description="Quantity.")
    dimensions: ContainerDimensionsResult | None = Field(default=None, alias="dimensions", description="Dimensions.")


class JobHandlingUnitResult(ResponseModel):
    """JobHandlingUnit response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    job_id: UUID | None = Field(default=None, alias="jobId", description="Job id.")
    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    is_active: bool | None = Field(default=None, alias="isActive", description="Is active.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    length: float | None = Field(default=None, alias="length", description="Length.")
    width: float | None = Field(default=None, alias="width", description="Width.")
    height: float | None = Field(default=None, alias="height", description="Height.")
    weight: float | None = Field(default=None, alias="weight", description="Weight.")
    container_type_id: int | None = Field(default=None, alias="containerTypeId", description="Container type id.")
    container_name: str | None = Field(default=None, alias="containerName", description="Container name.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    fill_rate: float | None = Field(default=None, alias="fillRate", description="Fill rate.")
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.")
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", description="Container thickness."
    )
    freight_class_id: UUID | None = Field(default=None, alias="freightClassId", description="Freight class id.")
    nmfc_item_no: str | None = Field(default=None, alias="nmfcItemNo", description="Nmfc item no.")
    labor_minutes: int | None = Field(default=None, alias="laborMinutes", description="Labor minutes.")
    declared_value: float | None = Field(default=None, alias="declaredValue", description="Declared value.")
    document_exists: bool | None = Field(default=None, alias="documentExists", description="Document exists.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    has_custom_name: bool | None = Field(default=None, alias="hasCustomName", description="Has custom name.")
    inventory_items: list[ContentInventoryItemResult] | None = Field(
        default=None, alias="inventoryItems", description="Inventory items."
    )
    content_handling_units: list[ContentHandlingUnitResult] | None = Field(
        default=None, alias="contentHandlingUnits", description="Content handling units."
    )
    materials: list[HandlingUnitMaterialResult] | None = Field(
        default=None, alias="materials", description="Materials."
    )
    container_handling_unit_material_id: int | None = Field(
        default=None, alias="containerHandlingUnitMaterialId", description="Container handling unit material id."
    )
    container_handling_unit_material: ContainerHandlingUnitMaterialResult | None = Field(
        default=None, alias="containerHandlingUnitMaterial", description="Container handling unit material."
    )
    material_total_cost: float | None = Field(
        default=None, alias="materialTotalCost", description="Material total cost."
    )
    is_used_in_shipment: bool | None = Field(default=None, alias="isUsedInShipment", description="Is used in shipment.")
    cubic_feet: float | None = Field(default=None, alias="cubicFeet", description="Cubic feet.")


class JobHandlingUnitListServiceResponseResult(ResponseModel):
    """JobHandlingUnitListServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: list[JobHandlingUnitResult] | None = Field(default=None, alias="data", description="Data.")


class FinalOverrideRequest(PackingRequestModel):
    """FinalOverrideProviderModel request contract from 8_01."""

    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")
    force_update: bool | None = Field(default=None, alias="forceUpdate", description="Force update.")
    provider_id: UUID | None = Field(default=None, alias="providerID", description="Provider id.")
    shipment_type: UUID | None = Field(default=None, alias="shipmentType", description="Shipment type.")
    provider_company_code: str | None = Field(
        default=None, alias="providerCompanyCode", description="Provider company code."
    )
    provider_company_name: str | None = Field(
        default=None, alias="providerCompanyName", description="Provider company name."
    )
    pro_num: str | None = Field(default=None, alias="proNum", description="Pro num.")
    freight_quote_options_id: UUID | None = Field(
        default=None, alias="freightQuoteOptionsId", description="Freight quote options id."
    )
    shipping_id: int | None = Field(default=None, alias="shippingId", description="Shipping id.")


class CreateOverriddenQuoteResponseResult(ResponseModel):
    """CreateOverriddenQuoteResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")
    freight_quote_options_id: UUID | None = Field(
        default=None, alias="freightQuoteOptionsId", description="Freight quote options id."
    )
    shipping_id: int | None = Field(default=None, alias="shippingId", description="Shipping id.")
    task_modified_date: datetime | None = Field(
        default=None, alias="taskModifiedDate", description="Task modified date."
    )


class JobTransportationHandlingUnitInput(PackingRequestModel):
    """JobTransportationHandlingUnit request contract from 8_01."""

    quantity: int | None = Field(default=None, alias="quantity", description="Quantity.")
    id: int | None = Field(default=None, alias="id", description="Id.")


class SelectRateQuoteRequest(PackingRequestModel):
    """SelectRateModel request contract from 8_01."""

    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")
    force_update: bool | None = Field(default=None, alias="forceUpdate", description="Force update.")
    rates_key: str = Field(alias="ratesKey", description="Rates key.", min_length=1)
    carrier_code: str = Field(alias="carrierCode", description="Carrier code.", min_length=1)
    carrier_account_id: int | None = Field(default=None, alias="carrierAccountId", description="Carrier account id.")
    active: bool | None = Field(default=None, alias="active", description="Active.")
    pickup_agent_id: UUID | None = Field(default=None, alias="pickupAgentId", description="Pickup agent id.")
    job_id: UUID | None = Field(default=None, alias="jobId", description="Job id.")
    shipping_id: int | None = Field(default=None, alias="shippingId", description="Shipping id.")
    handling_units: list[JobTransportationHandlingUnitInput] | None = Field(
        default=None, alias="handlingUnits", description="Handling units."
    )


class SaveRateQuoteResponseResult(ResponseModel):
    """SaveRateQuoteResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")
    transportation_quote: TransportationQuoteResult | None = Field(
        default=None, alias="transportationQuote", description="Transportation quote."
    )


class CarrierAccountInfoInput(PackingRequestModel):
    """CarrierAccountInfo request contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    key: str | None = Field(default=None, alias="key", description="Key.")
    friendly_name: str | None = Field(default=None, alias="friendlyName", description="Friendly name.")


class TransportationQuoteInput(PackingRequestModel):
    """TransportationQuote request contract from 8_01."""

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
    used_carrier_account_info: CarrierAccountInfoInput | None = Field(
        default=None, alias="usedCarrierAccountInfo", description="Used carrier account info."
    )
    quote_snapshot: str | None = Field(default=None, alias="quoteSnapshot", description="Quote snapshot.")
    shipping_id: int | None = Field(default=None, alias="shippingId", description="Shipping id.")
    order_in_shipping: int | None = Field(default=None, alias="orderInShipping", description="Order in shipping.")
    created_by: int | None = Field(default=None, alias="createdBy", description="Created by.")
    created_date: datetime | None = Field(default=None, alias="createdDate", description="Created date.")
    modified_by: int | None = Field(default=None, alias="modifiedBy", description="Modified by.")
    modified_date: datetime | None = Field(default=None, alias="modifiedDate", description="Modified date.")


class SaveFinalQuoteRequest(PackingRequestModel):
    """SaveFinalQuoteModel request contract from 8_01."""

    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")
    force_update: bool | None = Field(default=None, alias="forceUpdate", description="Force update.")
    quote: TransportationQuoteInput | None = Field(default=None, alias="quote", description="Quote.")


class JobModifiedDateServiceResponseResult(ResponseModel):
    """JobModifiedDateServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(default=None, alias="jobModifiedDate", description="Job modified date.")


class ShippingHistoryStatusResult(ResponseModel):
    """ShippingHistoryStatus response contract from 8_01."""

    city: str | None = Field(default=None, alias="city", description="City.")
    state: str | None = Field(default=None, alias="state", description="State.")
    country_code: str | None = Field(default=None, alias="countryCode", description="Country code.")
    country: str | None = Field(default=None, alias="country", description="Country.")
    display_status_message: str | None = Field(
        default=None, alias="displayStatusMessage", description="Display status message."
    )
    internal_status_code: Literal[1, 2, 3, 4] | None = Field(
        default=None, alias="internalStatusCode", description="Internal status code."
    )
    status_date: datetime | None = Field(default=None, alias="statusDate", description="Status date.")
    time_zone: Literal[0, 1, 2, 3] | None = Field(default=None, alias="timeZone", description="Time zone.")
    status_message: str | None = Field(default=None, alias="statusMessage", description="Status message.")
    reason_message: str | None = Field(default=None, alias="reasonMessage", description="Reason message.")
    status_code: str | None = Field(default=None, alias="statusCode", description="Status code.")
    status_type: str | None = Field(default=None, alias="statusType", description="Status type.")
    location: str | None = Field(default=None, alias="location", description="Location.")


class WeightInfoResult(ResponseModel):
    """WeightInfo response contract from 8_01."""

    pounds: float | None = Field(default=None, alias="pounds", description="Pounds.")
    original_weight: float | None = Field(default=None, alias="originalWeight", description="Original weight.")
    original_weight_measure_unit: str | None = Field(
        default=None, alias="originalWeightMeasureUnit", description="Original weight measure unit."
    )


class ShippingPackageInfoResult(ResponseModel):
    """ShippingPackageInfo response contract from 8_01."""

    tracking_number: str | None = Field(default=None, alias="trackingNumber", description="Tracking number.")
    weight: WeightInfoResult | None = Field(default=None, alias="weight", description="Weight.")


class CarrierShipmentDetails(ResponseModel):
    """ShipmentDetails response contract from 8_01."""

    pro_number: str | None = Field(default=None, alias="proNumber", description="Pro number.")
    used_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="usedAPI", description="Used api."
    )
    history_provider_name: str | None = Field(
        default=None, alias="historyProviderName", description="History provider name."
    )
    history_statuses: list[ShippingHistoryStatusResult] | None = Field(
        default=None, alias="historyStatuses", description="History statuses."
    )
    weight: WeightInfoResult | None = Field(default=None, alias="weight", description="Weight.")
    job_weight: WeightInfoResult | None = Field(default=None, alias="jobWeight", description="Job weight.")
    successfully: bool | None = Field(default=None, alias="successfully", description="Successfully.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    multiple_shipments: bool | None = Field(default=None, alias="multipleShipments", description="Multiple shipments.")
    packages: list[ShippingPackageInfoResult] | None = Field(default=None, alias="packages", description="Packages.")
    estimated_delivery: datetime | None = Field(
        default=None, alias="estimatedDelivery", description="Estimated delivery."
    )


class ShipmentTrackingDocumentResult(ResponseModel):
    """ShipmentTrackingDocument response contract from 8_01."""

    document_id: str | None = Field(default=None, alias="documentId", description="Document id.")
    document_path: str | None = Field(default=None, alias="documentPath", description="Document path.")
    document_description: str | None = Field(
        default=None, alias="documentDescription", description="Document description."
    )
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")


class JobInventoryItemInfoDataInput(PackingRequestModel):
    """JobInventoryItemInfoData request contract from 8_01."""

    commodity_id: int | None = Field(default=None, alias="commodityId", description="Commodity id.")
    noted_conditions: str | None = Field(default=None, alias="notedConditions", description="Noted conditions.")
    job_item_notes: str | None = Field(default=None, alias="jobItemNotes", description="Job item notes.")


class ServiceBaseResponseResult(ResponseModel):
    """ServiceBaseResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")


class JobServiceAddOnResult(ResponseModel):
    """JobServiceAddOn response contract from 8_01."""

    job_add_on_id: int | None = Field(default=None, alias="jobAddOnId", description="Job add on id.")
    id: int | None = Field(default=None, alias="id", description="Id.")
    unique_id: UUID | None = Field(default=None, alias="uniqueId", description="Unique id.")
    params: str | None = Field(default=None, alias="params", description="Params.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    description: str | None = Field(default=None, alias="description", description="Description.")
    api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="api", description="Api."
    )


class SaveJobServiceAddOnRequestInput(PackingRequestModel):
    """SaveJobServiceAddOnRequest request contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    params: str | None = Field(default=None, alias="params", description="Params.")


class JobServiceAddOnEntityResult(ResponseModel):
    """JobServiceAddOnEntity response contract from 8_01."""

    job_add_on_id: int | None = Field(default=None, alias="jobAddOnId", description="Job add on id.")
    id: int | None = Field(default=None, alias="id", description="Id.")
    unique_id: UUID | None = Field(default=None, alias="uniqueId", description="Unique id.")
    params: str | None = Field(default=None, alias="params", description="Params.")
    carrier_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="carrierAPI", description="Carrier api."
    )


class JobServiceAddOnEntityListServiceResponseResult(ResponseModel):
    """JobServiceAddOnEntityListServiceResponse response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    data: list[JobServiceAddOnEntityResult] | None = Field(default=None, alias="data", description="Data.")


class ServiceAddOnPricingEntityResult(ResponseModel):
    """ServiceAddOnPricingEntity response contract from 8_01."""

    from_: float | None = Field(default=None, alias="from", description="From .")
    to: float | None = Field(default=None, alias="to", description="To.")


class ServiceAddOnGroupEntityResult(ResponseModel):
    """ServiceAddOnGroupEntity response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    pricing: ServiceAddOnPricingEntityResult | None = Field(default=None, alias="pricing", description="Pricing.")
    carrier_api: Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20] | None = Field(
        default=None, alias="carrierAPI", description="Carrier api."
    )
    name: str | None = Field(default=None, alias="name", description="Name.")
    description: str | None = Field(default=None, alias="description", description="Description.")


class ServiceAddOnEntityResult(ResponseModel):
    """ServiceAddOnEntity response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    group: ServiceAddOnGroupEntityResult | None = Field(default=None, alias="group", description="Group.")
    unique_id: UUID | None = Field(default=None, alias="uniqueId", description="Unique id.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    additional_description: str | None = Field(
        default=None, alias="additionalDescription", description="Additional description."
    )
    service_type: Literal[0, 1, 2] | None = Field(default=None, alias="serviceType", description="Service type.")


class CarrierShippingDocument(ResponseModel):
    """ShippingDocument response contract from 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    document_bytes: str | None = Field(default=None, alias="documentBytes", description="Document bytes.")
    document_type: str | None = Field(default=None, alias="documentType", description="Document type.")
    file_name: str | None = Field(default=None, alias="fileName", description="File name.")


class ShipmentFormPlan(ResponseModel):
    """FormsShipmentPlan response contract from 8_01."""

    job_shipment_id: UUID | None = Field(default=None, alias="jobShipmentID", description="Job shipment id.")
    job_id: UUID | None = Field(default=None, alias="jobID", description="Job id.")
    from_address_id: int | None = Field(default=None, alias="fromAddressId", description="From address id.")
    to_address_id: int | None = Field(default=None, alias="toAddressId", description="To address id.")
    provider_id: UUID | None = Field(default=None, alias="providerID", description="Provider id.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Sequence no.")
    from_location_company_name: str | None = Field(
        default=None, alias="fromLocationCompanyName", description="From location company name."
    )
    to_location_company_name: str | None = Field(
        default=None, alias="toLocationCompanyName", description="To location company name."
    )
    transport_type: str | None = Field(default=None, alias="transportType", description="Transport type.")
    provider_company_name: str | None = Field(
        default=None, alias="providerCompanyName", description="Provider company name."
    )
    freight_quote_options_id: UUID | None = Field(
        default=None, alias="freightQuoteOptionsId", description="Freight quote options id."
    )


class EditableFormContent(ResponseModel):
    """EditableFormContentResponseModel response contract from 8_01."""

    html_markup_content: str | None = Field(default=None, alias="htmlMarkupContent", description="Html markup content.")
    markup_styles: str | None = Field(default=None, alias="markupStyles", description="Markup styles.")


class GetMaterialsParams(RequestModel):
    """Query parameters for /api/company/{companyId}/materials."""

    only_active: bool | None = Field(None, alias="OnlyActive", description="OnlyActive filter.")


class ShipmentHistoryParams(RequestModel):
    """Query parameters for /api/job/{jobDisplayId}/tracking/shipment-history/{proNumber}."""

    quote_id: UUID | None = Field(None, alias="QuoteId", description="QuoteId filter.")


class ShipmentDocumentsParams(RequestModel):
    """Query parameters for /api/job/{jobDisplayId}/tracking/shipment-documents/{proNumber}."""

    quote_id: UUID | None = Field(None, alias="QuoteId", description="QuoteId filter.")


class GetAddonsParams(RequestModel):
    """Query parameters for /api/lookup/addOns."""

    carrier_apis: list[Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20]] | None = Field(
        None, alias="carrierAPIs", description="carrierAPIs filter."
    )


class GetQuotesParams(RequestModel):
    """Query parameters for /api/job/{jobDisplayId}/freightproviders."""

    shipment_types: list[UUID] | None = Field(None, alias="ShipmentTypes", description="ShipmentTypes filter.")
    active: bool | None = Field(None, alias="Active", description="Active filter.")
    is_overridden: bool | None = Field(None, alias="IsOverridden", description="IsOverridden filter.")
    carrier_apis: list[Literal[0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 20]] | None = Field(
        None, alias="CarrierAPIs", description="CarrierAPIs filter."
    )
    shipped: bool | None = Field(None, alias="Shipped", description="Shipped filter.")


CommonInventory.model_rebuild()
CommonInventoryRequest.model_rebuild()
MasterMaterialInfoResult.model_rebuild()
MaterialResult.model_rebuild()
PackInventoryItemModelInput.model_rebuild()
SuggestedHandlingUnitServiceResponseResult.model_rebuild()
SuggestedHandlingUnitResult.model_rebuild()
PendingHandlingUnitMaterialResult.model_rebuild()
PackHierarchyHandlingUnitModelInput.model_rebuild()
AddContentHandlingUnitModelInput.model_rebuild()
SuggestedHierarchyHandlingUnitListServiceResponseResult.model_rebuild()
SuggestedHierarchyHandlingUnitResult.model_rebuild()
PendingPackItemResult.model_rebuild()
ContentHandlingUnitResult.model_rebuild()
SuggestedCombinedHandlingUnitListServiceResponseResult.model_rebuild()
SuggestedCombinedHandlingUnitResult.model_rebuild()
AddedPendingPackItemResult.model_rebuild()
GetHandlingUnitMaterialsModelInput.model_rebuild()
PackagingItemDataInput.model_rebuild()
HandlingUnitMaterialsResponseServiceResponseResult.model_rebuild()
HandlingUnitMaterialsResponseResult.model_rebuild()
ContainerInformationResult.model_rebuild()
ValidateHandlingUnitBaseResultResult.model_rebuild()
ValidateHandlingUnitModelInput.model_rebuild()
ContainerDimensionsInput.model_rebuild()
ValidateHandlingUnitResultResult.model_rebuild()
PackHandlingUnitsModelInput.model_rebuild()
HandlingUnitPackagingInformationInput.model_rebuild()
JobHandlingUnitListServiceResponseResult.model_rebuild()
JobHandlingUnitResult.model_rebuild()
ContentInventoryItemResult.model_rebuild()
HandlingUnitMaterialResult.model_rebuild()
ContainerHandlingUnitMaterialResult.model_rebuild()
ContainerDimensionsResult.model_rebuild()
FinalOverrideRequest.model_rebuild()
CreateOverriddenQuoteResponseResult.model_rebuild()
SelectRateQuoteRequest.model_rebuild()
JobTransportationHandlingUnitInput.model_rebuild()
SaveRateQuoteResponseResult.model_rebuild()
TransportationQuoteResult.model_rebuild()
CarrierAccountInfoResult.model_rebuild()
SaveFinalQuoteRequest.model_rebuild()
TransportationQuoteInput.model_rebuild()
CarrierAccountInfoInput.model_rebuild()
JobModifiedDateServiceResponseResult.model_rebuild()
CarrierShipmentDetails.model_rebuild()
ShippingHistoryStatusResult.model_rebuild()
WeightInfoResult.model_rebuild()
ShippingPackageInfoResult.model_rebuild()
ShipmentTrackingDocumentResult.model_rebuild()
JobInventoryItemInfoDataInput.model_rebuild()
ServiceBaseResponseResult.model_rebuild()
JobServiceAddOnResult.model_rebuild()
SaveJobServiceAddOnRequestInput.model_rebuild()
JobServiceAddOnEntityListServiceResponseResult.model_rebuild()
JobServiceAddOnEntityResult.model_rebuild()
ServiceAddOnEntityResult.model_rebuild()
ServiceAddOnGroupEntityResult.model_rebuild()
ServiceAddOnPricingEntityResult.model_rebuild()
CarrierShippingDocument.model_rebuild()
ShipmentFormPlan.model_rebuild()
EditableFormContent.model_rebuild()


class HandlingUnitContainerTypeResult(ResponseModel):
    """HandlingUnitContainerType response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    code: str | None = Field(default=None, alias="code", description="Code.")
    short_code: str | None = Field(default=None, alias="shortCode", description="Short code.")
    is_active: bool | None = Field(default=None, alias="isActive", description="Is active.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    display_order_id: int | None = Field(default=None, alias="displayOrderId", description="Display order id.")
    priority: int | None = Field(default=None, alias="priority", description="Priority.")


class HandlingUnitContainerTypeGroupResult(ResponseModel):
    """HandlingUnitContainerTypeGroup response contract from 8_01."""

    id: int | None = Field(default=None, alias="id", description="Id.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    unique_id: UUID | None = Field(default=None, alias="uniqueId", description="Unique id.")
    display_order_id: int | None = Field(default=None, alias="displayOrderId", description="Display order id.")
    container_types: list[HandlingUnitContainerTypeResult] | None = Field(
        default=None, alias="containerTypes", description="Container types."
    )


class CPackEntityResult(ResponseModel):
    """CPackEntity response contract from 8_01."""

    id: UUID | None = Field(default=None, alias="id", description="Id.")
    name: str | None = Field(default=None, alias="name", description="Name.")
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Inches to add.")


class LookupFillResult(ResponseModel):
    """LookupFill response contract from 8_01."""

    fill_id: int | None = Field(default=None, alias="fillId", description="Fill id.")
    code: str | None = Field(default=None, alias="code", description="Code.")
    description: str | None = Field(default=None, alias="description", description="Description.")
    default_percent: float | None = Field(default=None, alias="defaultPercent", description="Default percent.")


class ContainerTypesParams(RequestModel):
    """Company-specific available container types."""

    company_id: UUID | None = Field(None, alias="companyId", description="Company UUID.")
