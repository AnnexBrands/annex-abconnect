"""ABConnect 8_01 inventory, packing, and shipping contracts.

Checked against the server release DTOs and bundled ACPortal schema. Explicit
nulls in these write models clear nullable values; omitted fields stay omitted.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel


class PackingRequestModel(RequestModel):
    """Strict packing input retaining explicit nulls for nullable server fields."""

    @classmethod
    def check(cls, data: Any, exclude_unset: bool = True) -> Any:
        """Validate before transport without dropping explicit field clears."""
        if isinstance(data, list):
            return [cls.check(item, exclude_unset=exclude_unset) for item in data]
        return cls.model_validate(data).model_dump(
            by_alias=True,
            exclude_unset=exclude_unset,
            mode="json",
        )


class JobInventoryItemModel(PackingRequestModel):
    """JobInventoryItemModel contract from server release 8_01."""

    sequence_no: int = Field(alias="sequenceNo", ge=1, le=1000, description="Display sequence within the job.")
    quantity: int = Field(alias="quantity", ge=1, le=9999999, description="Number of physical items or handling units.")
    name: str | None = Field(default=None, alias="name", max_length=250, description="Display name.")
    is_active: bool = Field(alias="isActive", description="Whether this record participates in active packing.")
    length: float | None = Field(default=None, alias="length", ge=0, le=9999, description="Length in inches.")
    width: float | None = Field(default=None, alias="width", ge=0, le=9999, description="Width in inches.")
    height: float | None = Field(default=None, alias="height", ge=0, le=9999, description="Height in inches.")
    weight: float | None = Field(default=None, alias="weight", ge=0, le=999999, description="Weight in pounds.")
    value: float | None = Field(
        default=None, alias="value", ge=0, le=9999999.99, description="Declared inventory value."
    )
    c_pack_id: UUID | None = Field(default=None, alias="cPackId", description="CPack definition UUID.")
    eccn: str | None = Field(
        default=None, alias="eccn", max_length=16, description="Export Control Classification Number."
    )
    schedule_b: str | None = Field(
        default=None, alias="scheduleB", max_length=16, description="Schedule B export classification."
    )
    customer_item_id: str | None = Field(
        default=None, alias="customerItemId", max_length=50, description="Customer-supplied item reference."
    )
    item_notes: str | None = Field(
        default=None, alias="itemNotes", max_length=250, description="Inventory notes, up to 250 characters."
    )
    noted_conditions: str | None = Field(
        default=None,
        alias="notedConditions",
        max_length=250,
        description="Observed inventory condition, up to 250 characters.",
    )
    auto_pack_off: bool = Field(
        default=False, alias="autoPackOff", description="Disable automatic packing for this inventory item."
    )
    parent_inventory_item_id: int | None = Field(
        default=None,
        alias="parentInventoryItemId",
        description="Parent inventory record ID, or null to clear the relationship.",
    )
    common_inventory_item_id: int | None = Field(
        default=None, alias="commonInventoryItemId", description="Company common-inventory record ID."
    )
    labor_minutes: int = Field(
        default=0, alias="laborMinutes", ge=0, le=6000000, description="Estimated packing labor in minutes."
    )
    commodity_id: int | None = Field(default=None, alias="commodityId", description="Commodity classification ID.")


class JobInventoryItem(ResponseModel):
    """JobInventoryItem contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    job_id: UUID | None = Field(default=None, alias="jobId", description="Owning job UUID.")
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Display sequence within the job.")
    quantity: int | None = Field(
        default=None, alias="quantity", description="Number of physical items or handling units."
    )
    name: str | None = Field(default=None, alias="name", description="Display name.")
    is_active: bool | None = Field(
        default=None, alias="isActive", description="Whether this record participates in active packing."
    )
    length: float | None = Field(default=None, alias="length", description="Length in inches.")
    width: float | None = Field(default=None, alias="width", description="Width in inches.")
    height: float | None = Field(default=None, alias="height", description="Height in inches.")
    weight: float | None = Field(default=None, alias="weight", description="Weight in pounds.")
    value: float | None = Field(default=None, alias="value", description="Declared inventory value.")
    c_pack_id: UUID | None = Field(default=None, alias="cPackId", description="CPack definition UUID.")
    eccn: str | None = Field(default=None, alias="eccn", description="Export Control Classification Number.")
    schedule_b: str | None = Field(default=None, alias="scheduleB", description="Schedule B export classification.")
    customer_item_id: str | None = Field(
        default=None, alias="customerItemId", description="Customer-supplied item reference."
    )
    item_notes: str | None = Field(
        default=None, alias="itemNotes", description="Inventory notes, up to 250 characters."
    )
    noted_conditions: str | None = Field(
        default=None, alias="notedConditions", description="Observed inventory condition, up to 250 characters."
    )
    auto_pack_off: bool | None = Field(
        default=None, alias="autoPackOff", description="Disable automatic packing for this inventory item."
    )
    document_exists: bool | None = Field(default=None, alias="documentExists", description="Document exists.")
    parent_inventory_item_id: int | None = Field(
        default=None,
        alias="parentInventoryItemId",
        description="Parent inventory record ID, or null to clear the relationship.",
    )
    common_inventory_item_id: int | None = Field(
        default=None, alias="commonInventoryItemId", description="Company common-inventory record ID."
    )
    labor_minutes: int | None = Field(
        default=None, alias="laborMinutes", description="Estimated packing labor in minutes."
    )
    commodity_id: int | None = Field(default=None, alias="commodityId", description="Commodity classification ID.")
    cubic_feet: float | None = Field(default=None, alias="cubicFeet", description="Cubic feet.")


class ContentHandlingUnitModel(PackingRequestModel):
    """ContentHandlingUnitModel contract from server release 8_01."""

    count: int = Field(
        default=0, alias="count", ge=0, le=9999999, description="Quantity assigned to the parent handling unit."
    )


class AddContentHandlingUnitModel(ContentHandlingUnitModel):
    """AddContentHandlingUnitModel contract from server release 8_01."""

    id: int = Field(default=0, alias="id", description="Identifier of this record; scoped to the job.")


class InventoryModel(PackingRequestModel):
    """InventoryModel contract from server release 8_01."""

    count: int = Field(
        default=0, alias="count", ge=0, le=9999999, description="Quantity assigned to the parent handling unit."
    )


class AddInventoryModel(InventoryModel):
    """AddInventoryModel contract from server release 8_01."""

    id: int = Field(default=0, alias="id", description="Identifier of this record; scoped to the job.")


class JobHandlingUnitModel(PackingRequestModel):
    """JobHandlingUnitModel contract from server release 8_01."""

    quantity: int = Field(alias="quantity", ge=1, le=9999999, description="Number of physical items or handling units.")
    is_active: bool = Field(alias="isActive", description="Whether this record participates in active packing.")
    sequence_no: int = Field(alias="sequenceNo", ge=0, le=1000, description="Display sequence within the job.")
    length: float | None = Field(default=None, alias="length", ge=0, le=9999, description="Length in inches.")
    width: float | None = Field(default=None, alias="width", ge=0, le=9999, description="Width in inches.")
    height: float | None = Field(default=None, alias="height", ge=0, le=9999, description="Height in inches.")
    weight: float | None = Field(default=None, alias="weight", ge=0, le=999999, description="Weight in pounds.")
    container_type_id: int | None = Field(
        default=None, alias="containerTypeId", description="Handling-unit container type ID."
    )
    fill_id: int | None = Field(default=None, alias="fillId", description="Packing fill material ID.")
    fill_rate: float | None = Field(
        default=None, alias="fillRate", ge=0, le=100, description="Packing fill percentage, from 0 through 100."
    )
    inches_to_add: float | None = Field(
        default=None, alias="inchesToAdd", ge=0, le=1000, description="Packing allowance in inches."
    )
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", ge=0, le=99, description="Container wall thickness in inches."
    )
    freight_class_id: UUID | None = Field(
        default=None, alias="freightClassId", description="Freight classification UUID."
    )
    nmfc_item_no: str | None = Field(
        default=None,
        alias="nmfcItemNo",
        max_length=50,
        description="National Motor Freight Classification item number.",
    )
    labor_minutes: int | None = Field(
        default=None, alias="laborMinutes", ge=0, le=6000000, description="Estimated packing labor in minutes."
    )
    declared_value: float | None = Field(
        default=None, alias="declaredValue", ge=0, le=9999999.99, description="Declared handling-unit value."
    )
    name: str | None = Field(default=None, alias="name", max_length=250, description="Display name.")
    has_custom_name: bool = Field(
        default=False, alias="hasCustomName", description="Whether the display name was supplied by the caller."
    )


class AddJobHandlingUnitModel(JobHandlingUnitModel):
    """AddJobHandlingUnitModel contract from server release 8_01."""

    content_handling_units: list[AddContentHandlingUnitModel] | None = Field(
        default=None, alias="contentHandlingUnits", description="Nested handling units and their assigned quantities."
    )
    inventory_items: list[AddInventoryModel] | None = Field(
        default=None,
        alias="inventoryItems",
        description="Inventory records and quantities contained by this handling unit.",
    )


class ContentInventoryItem(ResponseModel):
    """ContentInventoryItem contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    count: int | None = Field(default=None, alias="count", description="Quantity assigned to the parent handling unit.")


class ContentHandlingUnit(ResponseModel):
    """ContentHandlingUnit contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    count: int | None = Field(default=None, alias="count", description="Quantity assigned to the parent handling unit.")


class HandlingUnitMaterial(ResponseModel):
    """HandlingUnitMaterial contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    material_id: int | None = Field(default=None, alias="materialId", description="Company material definition ID.")
    material_name: str | None = Field(default=None, alias="materialName", description="Material name.")
    material_description: str | None = Field(
        default=None, alias="materialDescription", description="Material description."
    )
    quantity_planned: float | None = Field(
        default=None, alias="quantityPlanned", description="Planned material quantity."
    )
    unit_cost: float | None = Field(default=None, alias="unitCost", description="Cost per material unit.")
    added_by_auto_packer: bool | None = Field(
        default=None, alias="addedByAutoPacker", description="Whether automatic packing added this material."
    )
    waste_quantity: float | None = Field(
        default=None, alias="wasteQuantity", description="Material quantity consumed as waste."
    )
    quantity: float | None = Field(
        default=None, alias="quantity", description="Number of physical items or handling units."
    )


class ContainerDimensions(ResponseModel):
    """ContainerDimensions contract from server release 8_01."""

    length: float | None = Field(default=None, alias="length", description="Length in inches.")
    width: float | None = Field(default=None, alias="width", description="Width in inches.")
    height: float | None = Field(default=None, alias="height", description="Height in inches.")


class ContainerHandlingUnitMaterial(HandlingUnitMaterial):
    """ContainerHandlingUnitMaterial contract from server release 8_01."""

    dimensions: ContainerDimensions | None = Field(default=None, alias="dimensions", description="Dimensions.")


class JobHandlingUnit(ResponseModel):
    """JobHandlingUnit contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    job_id: UUID | None = Field(default=None, alias="jobId", description="Owning job UUID.")
    quantity: int | None = Field(
        default=None, alias="quantity", description="Number of physical items or handling units."
    )
    is_active: bool | None = Field(
        default=None, alias="isActive", description="Whether this record participates in active packing."
    )
    sequence_no: int | None = Field(default=None, alias="sequenceNo", description="Display sequence within the job.")
    length: float | None = Field(default=None, alias="length", description="Length in inches.")
    width: float | None = Field(default=None, alias="width", description="Width in inches.")
    height: float | None = Field(default=None, alias="height", description="Height in inches.")
    weight: float | None = Field(default=None, alias="weight", description="Weight in pounds.")
    container_type_id: int | None = Field(
        default=None, alias="containerTypeId", description="Handling-unit container type ID."
    )
    container_name: str | None = Field(default=None, alias="containerName", description="Container name.")
    fill_id: int | None = Field(default=None, alias="fillId", description="Packing fill material ID.")
    fill_rate: float | None = Field(
        default=None, alias="fillRate", description="Packing fill percentage, from 0 through 100."
    )
    inches_to_add: float | None = Field(default=None, alias="inchesToAdd", description="Packing allowance in inches.")
    container_thickness: float | None = Field(
        default=None, alias="containerThickness", description="Container wall thickness in inches."
    )
    freight_class_id: UUID | None = Field(
        default=None, alias="freightClassId", description="Freight classification UUID."
    )
    nmfc_item_no: str | None = Field(
        default=None, alias="nmfcItemNo", description="National Motor Freight Classification item number."
    )
    labor_minutes: int | None = Field(
        default=None, alias="laborMinutes", description="Estimated packing labor in minutes."
    )
    declared_value: float | None = Field(
        default=None, alias="declaredValue", description="Declared handling-unit value."
    )
    document_exists: bool | None = Field(default=None, alias="documentExists", description="Document exists.")
    name: str | None = Field(default=None, alias="name", description="Display name.")
    has_custom_name: bool | None = Field(
        default=None, alias="hasCustomName", description="Whether the display name was supplied by the caller."
    )
    inventory_items: list[ContentInventoryItem] | None = Field(
        default=None,
        alias="inventoryItems",
        description="Inventory records and quantities contained by this handling unit.",
    )
    content_handling_units: list[ContentHandlingUnit] | None = Field(
        default=None, alias="contentHandlingUnits", description="Nested handling units and their assigned quantities."
    )
    materials: list[HandlingUnitMaterial] | None = Field(
        default=None, alias="materials", description="Complete material arrangement for this handling unit."
    )
    container_handling_unit_material_id: int | None = Field(
        default=None,
        alias="containerHandlingUnitMaterialId",
        description="Assigned handling-unit material row ID, or null to clear.",
    )
    container_handling_unit_material: ContainerHandlingUnitMaterial | None = Field(
        default=None, alias="containerHandlingUnitMaterial", description="Container handling unit material."
    )
    material_total_cost: float | None = Field(
        default=None, alias="materialTotalCost", description="Material total cost."
    )
    is_used_in_shipment: bool | None = Field(default=None, alias="isUsedInShipment", description="Is used in shipment.")
    cubic_feet: float | None = Field(default=None, alias="cubicFeet", description="Cubic feet.")


class JobHandlingUnitDetails(JobHandlingUnit):
    """JobHandlingUnitDetails contract from server release 8_01."""

    pass


class HandlingUnitMaterialModel(PackingRequestModel):
    """HandlingUnitMaterialModel contract from server release 8_01."""

    material_id: int = Field(default=0, alias="materialId", description="Company material definition ID.")
    quantity_planned: float = Field(default=0.0, alias="quantityPlanned", description="Planned material quantity.")
    unit_cost: float = Field(default=0.0, alias="unitCost", description="Cost per material unit.")
    added_by_auto_packer: bool = Field(
        default=False, alias="addedByAutoPacker", description="Whether automatic packing added this material."
    )
    waste_quantity: float = Field(
        default=0.0, alias="wasteQuantity", description="Material quantity consumed as waste."
    )


class ManageableHandlingUnitMaterialModel(HandlingUnitMaterialModel):
    """ManageableHandlingUnitMaterialModel contract from server release 8_01."""

    id: int = Field(default=0, alias="id", description="Identifier of this record; scoped to the job.")


class ManageableJobHandlingUnitModel(JobHandlingUnitModel):
    """ManageableJobHandlingUnitModel contract from server release 8_01."""

    id: int = Field(default=0, alias="id", description="Identifier of this record; scoped to the job.")
    container_handling_unit_material_id: int | None = Field(
        default=None,
        alias="containerHandlingUnitMaterialId",
        description="Assigned handling-unit material row ID, or null to clear.",
    )
    materials: list[ManageableHandlingUnitMaterialModel] | None = Field(
        default=None, alias="materials", description="Complete material arrangement for this handling unit."
    )
    content_handling_units: list[AddContentHandlingUnitModel] | None = Field(
        default=None, alias="contentHandlingUnits", description="Nested handling units and their assigned quantities."
    )


class ManageHandlingUnitsModel(PackingRequestModel):
    """ManageHandlingUnitsModel contract from server release 8_01."""

    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for conflict detection.",
    )
    force_update: bool = Field(
        default=False,
        alias="forceUpdate",
        description="Override a modification conflict only when explicitly intended.",
    )
    handling_units: list[ManageableJobHandlingUnitModel] | None = Field(
        default=None, alias="handlingUnits", description="Complete handling-unit arrangement to manage."
    )


class ManageHandlingUnitsResponse(ResponseModel):
    """ManageHandlingUnitsResponse contract from server release 8_01."""

    success: bool | None = Field(default=None, alias="success", description="Success.")
    error_message: str | None = Field(default=None, alias="errorMessage", description="Error message.")
    job_modified_date: datetime | None = Field(
        default=None,
        alias="jobModifiedDate",
        description="Last observed job modification timestamp for conflict detection.",
    )
    handling_units: list[JobHandlingUnitDetails] | None = Field(
        default=None, alias="handlingUnits", description="Complete handling-unit arrangement to manage."
    )


class SetHandlingUnitContainerMaterialModel(PackingRequestModel):
    """SetHandlingUnitContainerMaterialModel contract from server release 8_01."""

    container_handling_unit_material_id: int | None = Field(
        default=None,
        alias="containerHandlingUnitMaterialId",
        description="Assigned handling-unit material row ID, or null to clear.",
    )


class JobTransportationHandlingUnit(ResponseModel):
    """JobTransportationHandlingUnit contract from server release 8_01."""

    quantity: int | None = Field(
        default=None, alias="quantity", description="Number of physical items or handling units."
    )
    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")


class Shipping(ResponseModel):
    """Shipping contract from server release 8_01."""

    id: int | None = Field(default=None, alias="id", description="Identifier of this record; scoped to the job.")
    name: str | None = Field(default=None, alias="name", description="Display name.")
    handling_units: list[JobTransportationHandlingUnit] | None = Field(
        default=None, alias="handlingUnits", description="Complete handling-unit arrangement to manage."
    )
    freight_quote_options: list[UUID] | None = Field(
        default=None, alias="freightQuoteOptions", description="Freight quote options."
    )
    is_archived: bool | None = Field(default=None, alias="isArchived", description="Is archived.")
