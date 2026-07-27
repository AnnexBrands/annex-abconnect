"""Lookup models for the ACPortal API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import Field

from ab.api.models.base import RequestModel, ResponseModel


class LookupItemsParams(RequestModel):
    """Query parameters for GET /lookup/items."""

    job_display_id: Optional[int] = Field(None, alias="jobDisplayId", description="Job display ID for item lookup")
    job_item_id: Optional[str] = Field(None, alias="jobItemId", description="Job item UUID filter")


class LookupDocumentTypesParams(RequestModel):
    """Query parameters for GET /lookup/documentTypes."""

    document_source: Optional[str] = Field(None, alias="documentSource", description="Document source filter")


class LookupDensityClassMapParams(RequestModel):
    """Query parameters for GET /lookup/densityClassMap."""

    carrier_api: Optional[str] = Field(None, alias="carrierApi", description="Carrier API identifier")


class ContactTypeEntity(ResponseModel):
    """Contact type — GET /lookup/contactTypes."""

    id: Optional[int] = Field(None, description="Contact type ID")
    name: Optional[str] = Field(None, description="Contact type name")
    description: Optional[str] = Field(None, description="Description")
    value: Optional[str] = Field(None, description="Contact type value")


class CountryCodeDto(ResponseModel):
    """Country code — GET /lookup/countries."""

    code: Optional[str] = Field(None, description="ISO country code")
    name: Optional[str] = Field(None, description="Country name")
    id: Optional[str] = Field(None, description="Country UUID")
    iata_code: Optional[str] = Field(None, alias="iataCode", description="IATA country code")


class JobStatus(ResponseModel):
    """Job status entry — GET /lookup/jobStatuses."""

    id: Optional[int] = Field(None, description="Status ID")
    name: Optional[str] = Field(None, description="Status name")
    description: Optional[str] = Field(None, description="Description")
    key: Optional[str] = Field(None, description="Status key")
    value: Optional[str] = Field(None, description="Status value")


class LookupItem(ResponseModel):
    """Generic lookup item — GET /lookup/items."""

    id: Optional[str] = Field(None, description="Item UUID")
    name: Optional[str] = Field(None, description="Item name")


# ---- Extended lookup models (008) -----------------------------------------


class ReferCategoryHierarchy(ResponseModel):
    """A referral-category hierarchy row — GET /lookup/referCategoryHeirachy.

    Despite living under ``/lookup``, this endpoint does not return the generic
    ``{id, key, name, value}`` lookup shape. It returns a referral record with
    its category and sub-category denormalized, plus campaign and ownership
    fields. It shared :class:`LookupValue` with the neighbouring
    ``/lookup/referCategory`` (which genuinely is a plain lookup), so every
    field below was undeclared and the two endpoints overwrote each other's
    fixture.
    """

    job_id: Optional[str] = Field(None, alias="jobID", description="Job ID")
    refer_sub_category_id: Optional[str] = Field(
        None, alias="referSubCategoryID", description="Referral sub-category ID",
    )
    refer_category_id: Optional[str] = Field(
        None, alias="referCategoryID", description="Referral category ID",
    )
    refer_category_name: Optional[str] = Field(
        None, alias="referCategoryName", description="Referral category name",
    )
    refer_sub_category_name: Optional[str] = Field(
        None, alias="referSubCategoryName", description="Referral sub-category name",
    )
    create_by: Optional[str] = Field(None, alias="createBy", description="Created by")
    modify_by: Optional[str] = Field(None, alias="modifyBy", description="Modified by")
    create_date: Optional[datetime] = Field(None, alias="createDate", description="Created date")
    # Spelled "modifiedDdate" on the wire — a server-side typo, mirrored here so
    # the alias matches what actually arrives.
    modified_date: Optional[datetime] = Field(
        None, alias="modifiedDdate", description="Modified date",
    )
    is_active: Optional[bool] = Field(None, alias="isActive", description="Whether active")
    refer_url: Optional[str] = Field(None, alias="referUrl", description="Referral URL")
    landing_url: Optional[str] = Field(None, alias="landingUrl", description="Landing URL")
    submission_url: Optional[str] = Field(
        None, alias="submissionUrl", description="Submission URL",
    )
    direct_email: Optional[str] = Field(None, alias="directEmail", description="Direct email")
    company_id: Optional[str] = Field(None, alias="companyID", description="Company ID")
    contact_id: Optional[str] = Field(None, alias="contactID", description="Contact ID")
    industry_type_id: Optional[str] = Field(
        None, alias="industryTypeID", description="Industry type ID",
    )
    industry_types: Optional[str] = Field(
        None, alias="industryTypes", description="Industry types",
    )
    action_type: Optional[str] = Field(None, alias="actionType", description="Action type")
    refered_internet_id: Optional[str] = Field(
        None, alias="referedInternetId", description="Referred internet ID",
    )
    is_paid: Optional[bool] = Field(None, alias="isPaid", description="Whether paid")


class LookupValue(ResponseModel):
    """Generic lookup value — GET /lookup/{masterConstantKey}.

    Source: MasterData.cs — controller returns id/key/name/value.
    """

    id: Optional[Union[str, int]] = Field(None, description="Value ID (Guid, or int for ContactTypes)")
    key: Optional[str] = Field(None, description="Master data key")
    name: Optional[str] = Field(None, description="Display name")
    value: Optional[str] = Field(None, description="Value (Guid)")


class AccessKey(ResponseModel):
    """Access key record — GET /lookup/accessKeys.

    Source: APIAccessKey.cs — accessKey/friendlyName fields.
    """

    access_key: Optional[str] = Field(None, alias="accessKey", description="Access key string")
    friendly_name: Optional[str] = Field(None, alias="friendlyName", description="Friendly display name")


class AccessKeySetup(ResponseModel):
    """Access key setup details — GET /lookup/accessKey/{accessKey}.

    Source: APIAccessKeySetup.cs — includes parent AccessKey fields.
    """

    access_key: Optional[str] = Field(None, alias="accessKey", description="Access key string")
    friendly_name: Optional[str] = Field(None, alias="friendlyName", description="Friendly display name")
    user_id: Optional[str] = Field(None, alias="userId", description="User ID (Guid)")
    user_identifier: Optional[int] = Field(None, alias="userIdentifier", description="User identifier (int)")
    referred_by_id: Optional[str] = Field(None, alias="referredById", description="Referred by ID (Guid)")
    referred_by: Optional[str] = Field(None, alias="referredBy", description="Referred by name")
    use_agent_search: Optional[bool] = Field(None, alias="useAgentSearch", description="Use agent search")
    allow_job_info_update: Optional[bool] = Field(None, alias="allowJobInfoUpdate", description="Allow job info update")
    allow_job_info_update_without_booking_key: Optional[bool] = Field(
        None, alias="allowJobInfoUpdateWithoutBookingKey", description="Allow update without booking key",
    )
    ip_protections: Optional[list] = Field(None, alias="ipProtections", description="IP protection rules")
    parcel_transportation_multiplier: Optional[float] = Field(
        None, alias="parcelTransportationMultiplier", description="Parcel transportation multiplier",
    )
    parcel_accessorial_multiplier: Optional[float] = Field(
        None, alias="parcelAccessorialMultiplier", description="Parcel accessorial multiplier",
    )
    items_combine_max_inches: Optional[int] = Field(
        None, alias="itemsCombineMaxInches", description="Max combine inches",
    )
    use_pack_labor_calculation: Optional[bool] = Field(
        None, alias="usePackLaborCalculation", description="Use pack labor calculation",
    )
    use_base_pickup_fee_calculation: Optional[bool] = Field(
        None, alias="useBasePickupFeeCalculation", description="Use base pickup fee calculation",
    )
    force_agent_pickup: Optional[bool] = Field(None, alias="forceAgentPickup", description="Force agent pickup")


class DocumentTypeBySource(ResponseModel):
    """Document type by source — GET /lookup/documentTypes.

    Source: DocumentTypeBySource.cs — name/value/documentSource fields.
    """

    name: Optional[str] = Field(None, description="Document type name")
    value: Optional[int] = Field(None, description="Document type value")
    document_source: Optional[int] = Field(None, alias="documentSource", description="Document source")


class PPCCampaign(ResponseModel):
    """PPC campaign — GET /lookup/PPCCampaigns.

    Source: PPCCampaign.cs — id/name fields.
    """

    id: Optional[int] = Field(None, description="Campaign ID")
    name: Optional[str] = Field(None, description="Campaign name")


class CommonInsuranceSlab(ResponseModel):
    """Common insurance slab — GET /lookup/comonInsurance.

    Source: Live API — insurance slab entity with rate/deductible fields.
    """

    id: Optional[str] = Field(None, description="Slab ID (Guid)")
    key: Optional[str] = Field(None, description="Slab key")
    name: Optional[str] = Field(None, description="Slab name")
    value: Optional[str] = Field(None, description="Slab value (Guid)")
    insurance_slab_id: Optional[str] = Field(None, alias="insuranceSlabID", description="Insurance slab ID (Guid)")
    transp_type_id: Optional[str] = Field(None, alias="transpTypeID", description="Transport type ID (Guid)")
    deductible_amount: Optional[float] = Field(None, alias="deductibleAmount", description="Deductible amount")
    is_active: Optional[bool] = Field(None, alias="isActive", description="Whether active")
    rate: Optional[float] = Field(None, description="Insurance rate")
    revision: Optional[int] = Field(None, description="Revision number")
    insurance_type: Optional[str] = Field(None, alias="insuranceType", description="Insurance type")


class ParcelPackageType(ResponseModel):
    """Parcel package type — GET /lookup/parcelPackageTypes.

    Source: Live API response — full package type entity.
    """

    id: Optional[int] = Field(None, description="Package type ID")
    name: Optional[str] = Field(None, description="Package type name")
    code: Optional[str] = Field(None, description="Package type code")
    description: Optional[str] = Field(None, description="Description")
    carrier_api: Optional[int] = Field(None, alias="carrierAPI", description="Carrier API identifier")
    carrier_code: Optional[str] = Field(None, alias="carrierCode", description="Carrier code")
    weight_limit: Optional[float] = Field(None, alias="weightLimit", description="Weight limit")
    length_limit: Optional[float] = Field(None, alias="lengthLimit", description="Length limit")
    width_limit: Optional[float] = Field(None, alias="widthLimit", description="Width limit")
    height_limit: Optional[float] = Field(None, alias="heightLimit", description="Height limit")
    priority: Optional[int] = Field(None, description="Priority")
    weight: Optional[float] = Field(None, description="Default weight")
    length: Optional[float] = Field(None, description="Default length")
    width: Optional[float] = Field(None, description="Default width")
    height: Optional[float] = Field(None, description="Default height")
    is_active: Optional[bool] = Field(None, alias="isActive", description="Whether active")
    cost: Optional[float] = Field(None, description="Cost")
    sell: Optional[float] = Field(None, description="Sell price")


class DensityClassEntry(ResponseModel):
    """Density-to-class mapping — GET /lookup/densityClassMap.

    Source: Live API — GuidSequentialRangeValue shape.
    """

    range_end: Optional[float] = Field(None, alias="rangeEnd", description="Range end value")
    value: Optional[str] = Field(None, description="Value (Guid)")
