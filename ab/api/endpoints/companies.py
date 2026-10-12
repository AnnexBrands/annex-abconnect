"""Companies API endpoints (24 routes)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ab.api.base import BaseEndpoint
from ab.api.models.release_support import (
    CommonInventory,
    CommonInventoryRequest,
    GetHandlingUnitMaterialsModelInput,
    HandlingUnitMaterialsResponseServiceResponseResult,
    JobHandlingUnitListServiceResponseResult,
    MasterMaterialInfoResult,
    MaterialResult,
    PackHandlingUnitsModelInput,
    PackHierarchyHandlingUnitModelInput,
    PackInventoryItemModelInput,
    SuggestedCombinedHandlingUnitListServiceResponseResult,
    SuggestedHandlingUnitServiceResponseResult,
    SuggestedHierarchyHandlingUnitListServiceResponseResult,
    ValidateHandlingUnitModelInput,
    ValidateHandlingUnitResultResult,
)
from ab.api.route import Route
from ab.cache import CodeResolver

if TYPE_CHECKING:
    from ab.api.models.companies import (
        BrandTree,
        CarrierAccount,
        CarrierAccountSaveRequest,
        CompanyBrand,
        CompanyDetails,
        CompanySearchRequest,
        CompanySimple,
        GeoSettings,
        GeoSettingsSaveRequest,
        PackagingLabor,
        PackagingLaborSaveRequest,
        PackagingSettings,
        PackagingSettingsSaveRequest,
        PackagingTariff,
        SearchCompanyResponse,
    )
    from ab.api.models.shared import ListRequest

_GET = Route("GET", "/companies/{id}", response_model="CompanySimple")
_GET_DETAILS = Route("GET", "/companies/{companyId}/details", response_model="CompanyDetails")
_GET_FULLDETAILS = Route("GET", "/companies/{companyId}/fulldetails", response_model="CompanyDetails")
_UPDATE_FULLDETAILS = Route(
    "PUT",
    "/companies/{companyId}/fulldetails",
    request_model="CompanyDetails",
    response_model="CompanyDetails",
)
_CREATE = Route("POST", "/companies/fulldetails", request_model="CompanyDetails", response_model="str")
_SEARCH = Route(
    "POST",
    "/companies/search/v2",
    request_model="CompanySearchRequest",
    response_model="List[SearchCompanyResponse]",
)
_LIST = Route("POST", "/companies/list", request_model="ListRequest", response_model="List[CompanySimple]")
_AVAILABLE = Route("GET", "/companies/availableByCurrentUser", response_model="List[CompanySimple]")

# Brands (008)
_GET_BRANDS = Route("GET", "/companies/brands", response_model="List[CompanyBrand]")
_GET_BRANDS_TREE = Route("GET", "/companies/brandstree", response_model="List[BrandTree]")

# Geo Settings (008)
_GET_GEO_AREA_COMPANIES = Route("GET", "/companies/geoAreaCompanies")
_GET_GEO_SETTINGS = Route("GET", "/companies/{companyId}/geosettings", response_model="GeoSettings")
_SAVE_GEO_SETTINGS = Route("POST", "/companies/{companyId}/geosettings", request_model="GeoSettingsSaveRequest")
_GET_GLOBAL_GEO_SETTINGS = Route(
    "GET",
    "/companies/geosettings",
    response_model="GeoSettings",
    params_model="GeoSettingsParams",
)

# Carrier Accounts (008)
_SEARCH_CARRIER_ACCOUNTS = Route(
    "GET",
    "/companies/search/carrier-accounts",
    params_model="CarrierAccountSearchParams",
)
_SUGGEST_CARRIERS = Route("GET", "/companies/suggest-carriers", params_model="SuggestCarriersParams")
_GET_CARRIER_ACCOUNTS = Route("GET", "/companies/{companyId}/carrierAcounts", response_model="List[CarrierAccount]")
_SAVE_CARRIER_ACCOUNTS = Route(
    "POST",
    "/companies/{companyId}/carrierAcounts",
    request_model="CarrierAccountSaveRequest",
)

# Packaging (008)
_GET_PACKAGING_SETTINGS = Route("GET", "/companies/{companyId}/packagingsettings", response_model="PackagingSettings")
_SAVE_PACKAGING_SETTINGS = Route(
    "POST", "/companies/{companyId}/packagingsettings", request_model="PackagingSettingsSaveRequest"
)
_GET_PACKAGING_LABOR = Route("GET", "/companies/{companyId}/packaginglabor", response_model="PackagingLabor")
_SAVE_PACKAGING_LABOR = Route(
    "POST", "/companies/{companyId}/packaginglabor", request_model="PackagingLaborSaveRequest"
)
_GET_INHERITED_PACKAGING_TARIFFS = Route(
    "GET",
    "/companies/{companyId}/inheritedPackagingTariffs",
    response_model="List[PackagingTariff]",
    params_model="InheritFromParams",
)
_GET_INHERITED_PACKAGING_LABOR = Route(
    "GET",
    "/companies/{companyId}/inheritedpackaginglabor",
    response_model="PackagingLabor",
    params_model="InheritFromParams",
)


_CURRENT_GET_INVENTORY = Route("GET", "/company/{companyId}/inventory", response_model="List[CommonInventory]")
_CURRENT_CREATE_INVENTORY = Route(
    "POST", "/company/{companyId}/inventory", request_model="CommonInventoryRequest", response_model="CommonInventory"
)
_CURRENT_UPDATE_INVENTORY = Route("PUT", "/company/{companyId}/inventory/{id}", request_model="CommonInventoryRequest")
_CURRENT_DELETE_INVENTORY = Route("DELETE", "/company/{companyId}/inventory/{id}")
_CURRENT_GET_MATERIALS = Route(
    "GET",
    "/company/{companyId}/materials",
    response_model="List[MasterMaterialInfoResult]",
    params_model="GetMaterialsParams",
)
_CURRENT_GET_DEFAULT_PALLET = Route(
    "GET", "/company/{companyId}/materials/default-pallet", response_model="MaterialResult"
)
_CURRENT_GET_STOCK_BOXES = Route(
    "GET", "/company/{companyId}/materials/stock-boxes", response_model="List[MaterialResult]"
)
_CURRENT_GET_D_CONTAINERS = Route(
    "GET", "/company/{companyId}/materials/d-containers", response_model="List[MaterialResult]"
)
_CURRENT_PACK_INVENTORY = Route(
    "POST",
    "/company/{companyId}/pack/inventory",
    request_model="PackInventoryItemModelInput",
    response_model="SuggestedHandlingUnitServiceResponseResult",
)
_CURRENT_PACK_HIERARCHY = Route(
    "POST",
    "/company/{companyId}/pack/hierarchy",
    request_model="List[PackHierarchyHandlingUnitModelInput]",
    response_model="SuggestedHierarchyHandlingUnitListServiceResponseResult",
)
_CURRENT_PACK_INVENTORIES = Route(
    "POST",
    "/company/{companyId}/pack/inventories",
    request_model="List[PackInventoryItemModelInput]",
    response_model="SuggestedCombinedHandlingUnitListServiceResponseResult",
)
_CURRENT_GET_HANDLING_UNIT_MATERIALS = Route(
    "POST",
    "/company/{companyId}/pack/handlingunit/materials",
    request_model="GetHandlingUnitMaterialsModelInput",
    response_model="HandlingUnitMaterialsResponseServiceResponseResult",
)
_CURRENT_VALIDATE_HANDLING_UNIT = Route(
    "POST",
    "/company/{companyId}/pack/validate",
    request_model="ValidateHandlingUnitModelInput",
    response_model="ValidateHandlingUnitResultResult",
)
_CURRENT_PACK_HANDLING_UNITS = Route(
    "POST",
    "/company/{companyId}/pack/handling-units",
    request_model="PackHandlingUnitsModelInput",
    response_model="JobHandlingUnitListServiceResponseResult",
)


class CompaniesEndpoint(BaseEndpoint):
    """Operations on companies (ACPortal API)."""

    def __init__(self, client: Any, resolver: CodeResolver) -> None:
        super().__init__(client)
        self._resolver = resolver

    def _resolve(self, code_or_id: str) -> str:
        return self._resolver.resolve(code_or_id)

    def get_by_id(self, company_id: str) -> CompanySimple:
        """GET /companies/{id}

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_by_id.html
        Response model: CompanySimple
        """
        return self._request(_GET.bind(id=self._resolve(company_id)))

    def get_details(self, company_id: str) -> CompanyDetails:
        """GET /companies/{companyId}/details

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_details.html
        Response model: CompanyDetails
        """
        return self._request(_GET_DETAILS.bind(companyId=self._resolve(company_id)))

    def get_fulldetails(self, company_id: str) -> CompanyDetails:
        """GET /companies/{companyId}/fulldetails

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_fulldetails.html
        Response model: CompanyDetails
        """
        return self._request(_GET_FULLDETAILS.bind(companyId=self._resolve(company_id)))

    def update_fulldetails(self, company_id: str, *, data: CompanyDetails | dict) -> CompanyDetails:
        """PUT /companies/{companyId}/fulldetails.

        Args:
            company_id: Company ID or code.
            data: Full company details payload.
                Accepts a :class:`CompanyDetails` instance or a dict.

        Request model: :class:`CompanyDetails`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/update_fulldetails.html
        Request model: CompanyDetails
        Response model: CompanyDetails
        """
        return self._request(
            _UPDATE_FULLDETAILS.bind(companyId=self._resolve(company_id)),
            json=data,
        )

    def create(self, *, data: CompanyDetails | dict) -> str:
        """POST /companies/fulldetails.

        Args:
            data: Full company details payload.
                Accepts a :class:`CompanyDetails` instance or a dict.

        Request model: :class:`CompanyDetails`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/create.html
        Request model: CompanyDetails
        """
        return self._request(_CREATE, json=data)

    def search(self, *, data: CompanySearchRequest | dict) -> list[SearchCompanyResponse]:
        """POST /companies/search/v2.

        Args:
            data: Search filter with pagination, search text, and filters.
                Accepts a :class:`CompanySearchRequest` instance or a dict.

        Request model: :class:`CompanySearchRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/search.html
        Request model: CompanySearchRequest
        Response model: List[SearchCompanyResponse]
        """
        return self._request(_SEARCH, json=data)

    def list(self, *, data: ListRequest | dict) -> list[CompanySimple]:
        """POST /companies/list.

        Args:
            data: List filter with pagination, sorting, and filters.
                Accepts a :class:`ListRequest` instance or a dict.

        Request model: :class:`ListRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/list.html
        Request model: ListRequest
        Response model: List[CompanySimple]
        """
        return self._request(_LIST, json=data)

    def available_by_current_user(self) -> list[CompanySimple]:
        """GET /companies/availableByCurrentUser

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/available_by_current_user.html
        Response model: List[CompanySimple]
        """
        return self._request(_AVAILABLE)

    # ---- Brands (008) -----------------------------------------------------

    def get_brands(self) -> list[CompanyBrand]:
        """GET /companies/brands

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_brands.html
        Response model: List[CompanyBrand]
        """
        return self._request(_GET_BRANDS)

    def get_brands_tree(self) -> list[BrandTree]:
        """GET /companies/brandstree

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_brands_tree.html
        Response model: List[BrandTree]
        """
        return self._request(_GET_BRANDS_TREE)

    # ---- Geo Settings (008) -----------------------------------------------

    def get_geo_area_companies(self, *, params: dict | None = None) -> None:
        """GET /companies/geoAreaCompanies.

        Args:
            params: Optional query parameters as a dict.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_geo_area_companies.html
        """
        return self._request(_GET_GEO_AREA_COMPANIES, params=params)

    def get_geo_settings(self, company_id: str) -> GeoSettings:
        """GET /companies/{companyId}/geosettings

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_geo_settings.html
        Response model: GeoSettings
        """
        return self._request(_GET_GEO_SETTINGS.bind(companyId=self._resolve(company_id)))

    def save_geo_settings(
        self,
        company_id: str,
        *,
        data: GeoSettingsSaveRequest | dict,
    ) -> None:
        """POST /companies/{companyId}/geosettings.

        Args:
            company_id: Company ID or code.
            data: Geo settings payload with service_areas and restrictions.
                Accepts a :class:`GeoSettingsSaveRequest` instance or a dict.

        Request model: :class:`GeoSettingsSaveRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/save_geo_settings.html
        Request model: GeoSettingsSaveRequest
        """
        return self._request(
            _SAVE_GEO_SETTINGS.bind(companyId=self._resolve(company_id)),
            json=data,
        )

    def get_global_geo_settings(self) -> GeoSettings:
        """GET /companies/geosettings

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_global_geo_settings.html
        Query params: GeoSettingsParams
        Response model: GeoSettings
        """
        return self._request(_GET_GLOBAL_GEO_SETTINGS)

    # ---- Carrier Accounts (008) -------------------------------------------

    def search_carrier_accounts(
        self,
        *,
        current_company_id: str | None = None,
        query: str | None = None,
    ) -> None:
        """GET /companies/search/carrier-accounts

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/search_carrier_accounts.html
        Query params: CarrierAccountSearchParams
        """
        return self._request(
            _SEARCH_CARRIER_ACCOUNTS,
            params=dict(current_company_id=current_company_id, query=query),
        )

    def suggest_carriers(self, *, tracking_number: str) -> None:
        """GET /companies/suggest-carriers

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/suggest_carriers.html
        Query params: SuggestCarriersParams
        """
        return self._request(_SUGGEST_CARRIERS, params=dict(tracking_number=tracking_number))

    def get_carrier_accounts(self, company_id: str) -> list[CarrierAccount]:
        """GET /companies/{companyId}/carrierAcounts

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_carrier_accounts.html
        Response model: List[CarrierAccount]
        """
        return self._request(_GET_CARRIER_ACCOUNTS.bind(companyId=self._resolve(company_id)))

    def save_carrier_accounts(self, company_id: str, *, data: CarrierAccountSaveRequest | dict) -> None:
        """POST /companies/{companyId}/carrierAcounts.

        Args:
            company_id: Company ID or code.
            data: Carrier account payload.
                Accepts a :class:`CarrierAccountSaveRequest` instance or a dict.

        Request model: :class:`CarrierAccountSaveRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/save_carrier_accounts.html
        Request model: CarrierAccountSaveRequest
        """
        return self._request(
            _SAVE_CARRIER_ACCOUNTS.bind(companyId=self._resolve(company_id)),
            json=data,
        )

    # ---- Packaging (008) --------------------------------------------------

    def get_packaging_settings(self, company_id: str) -> PackagingSettings:
        """GET /companies/{companyId}/packagingsettings

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_packaging_settings.html
        Response model: PackagingSettings
        """
        return self._request(_GET_PACKAGING_SETTINGS.bind(companyId=self._resolve(company_id)))

    def save_packaging_settings(self, company_id: str, *, data: PackagingSettingsSaveRequest | dict) -> None:
        """POST /companies/{companyId}/packagingsettings.

        Args:
            company_id: Company ID or code.
            data: Packaging settings payload.
                Accepts a :class:`PackagingSettingsSaveRequest` instance or a dict.

        Request model: :class:`PackagingSettingsSaveRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/save_packaging_settings.html
        Request model: PackagingSettingsSaveRequest
        """
        return self._request(
            _SAVE_PACKAGING_SETTINGS.bind(companyId=self._resolve(company_id)),
            json=data,
        )

    def get_packaging_labor(self, company_id: str) -> PackagingLabor:
        """GET /companies/{companyId}/packaginglabor

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_packaging_labor.html
        Response model: PackagingLabor
        """
        return self._request(_GET_PACKAGING_LABOR.bind(companyId=self._resolve(company_id)))

    def save_packaging_labor(self, company_id: str, *, data: PackagingLaborSaveRequest | dict) -> None:
        """POST /companies/{companyId}/packaginglabor.

        Args:
            company_id: Company ID or code.
            data: Packaging labor rates payload.
                Accepts a :class:`PackagingLaborSaveRequest` instance or a dict.

        Request model: :class:`PackagingLaborSaveRequest`

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/save_packaging_labor.html
        Request model: PackagingLaborSaveRequest
        """
        return self._request(
            _SAVE_PACKAGING_LABOR.bind(companyId=self._resolve(company_id)),
            json=data,
        )

    def get_inherited_packaging_tariffs(self, company_id: str) -> list[PackagingTariff]:
        """GET /companies/{companyId}/inheritedPackagingTariffs

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_inherited_packaging_tariffs.html
        Query params: InheritFromParams
        Response model: List[PackagingTariff]
        """
        return self._request(_GET_INHERITED_PACKAGING_TARIFFS.bind(companyId=self._resolve(company_id)))

    def get_inherited_packaging_labor(self, company_id: str) -> PackagingLabor:
        """GET /companies/{companyId}/inheritedpackaginglabor

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_inherited_packaging_labor.html
        Query params: InheritFromParams
        Response model: PackagingLabor
        """
        return self._request(_GET_INHERITED_PACKAGING_LABOR.bind(companyId=self._resolve(company_id)))

    # ---- Backwards Compatibility Aliases ------------------------------------

    def get(self, company_id: str) -> CompanyDetails:
        """Alias for :meth:`get_fulldetails`."""
        return self.get_fulldetails(company_id)

    def available(self) -> list[CompanySimple]:
        """Alias for :meth:`available_by_current_user`."""
        return self.available_by_current_user()

    def get_inventory(self, company_id: str) -> list[CommonInventory]:
        """GET /company/{companyId}/inventory.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_inventory.html
        Response model: List[CommonInventory]
        """
        return self._request(_CURRENT_GET_INVENTORY.bind(companyId=company_id))

    def create_inventory(self, company_id: str, *, data: CommonInventoryRequest | dict) -> CommonInventory:
        """POST /company/{companyId}/inventory.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/create_inventory.html
        Request model: CommonInventoryRequest
        Response model: CommonInventory
        """
        return self._request(_CURRENT_CREATE_INVENTORY.bind(companyId=company_id), json=data)

    def update_inventory(self, company_id: str, id: int, *, data: CommonInventoryRequest | dict) -> None:
        """PUT /company/{companyId}/inventory/{id}.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/update_inventory.html
        Request model: CommonInventoryRequest
        """
        return self._request(_CURRENT_UPDATE_INVENTORY.bind(companyId=company_id, id=id), json=data)

    def delete_inventory(self, company_id: str, id: int) -> None:
        """DELETE /company/{companyId}/inventory/{id}.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/delete_inventory.html
        """
        return self._request(_CURRENT_DELETE_INVENTORY.bind(companyId=company_id, id=id))

    def get_materials(self, company_id: str, *, only_active: bool | None = None) -> list[MasterMaterialInfoResult]:
        """GET /company/{companyId}/materials.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_materials.html
        Query params: GetMaterialsParams
        Response model: List[MasterMaterialInfoResult]
        """
        return self._request(_CURRENT_GET_MATERIALS.bind(companyId=company_id), params=dict(only_active=only_active))

    def get_default_pallet(self, company_id: str) -> MaterialResult:
        """GET /company/{companyId}/materials/default-pallet.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_default_pallet.html
        Response model: MaterialResult
        """
        return self._request(_CURRENT_GET_DEFAULT_PALLET.bind(companyId=company_id))

    def get_stock_boxes(self, company_id: str) -> list[MaterialResult]:
        """GET /company/{companyId}/materials/stock-boxes.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_stock_boxes.html
        Response model: List[MaterialResult]
        """
        return self._request(_CURRENT_GET_STOCK_BOXES.bind(companyId=company_id))

    def get_d_containers(self, company_id: str) -> list[MaterialResult]:
        """GET /company/{companyId}/materials/d-containers.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_d_containers.html
        Response model: List[MaterialResult]
        """
        return self._request(_CURRENT_GET_D_CONTAINERS.bind(companyId=company_id))

    def pack_inventory(
        self, company_id: str, *, data: PackInventoryItemModelInput | dict
    ) -> SuggestedHandlingUnitServiceResponseResult:
        """POST /company/{companyId}/pack/inventory.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/pack_inventory.html
        Request model: PackInventoryItemModelInput
        Response model: SuggestedHandlingUnitServiceResponseResult
        """
        return self._request(_CURRENT_PACK_INVENTORY.bind(companyId=company_id), json=data)

    def pack_hierarchy(
        self, company_id: str, *, data: list[PackHierarchyHandlingUnitModelInput] | list[dict]
    ) -> SuggestedHierarchyHandlingUnitListServiceResponseResult:
        """POST /company/{companyId}/pack/hierarchy.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/pack_hierarchy.html
        Request model: List[PackHierarchyHandlingUnitModelInput]
        Response model: SuggestedHierarchyHandlingUnitListServiceResponseResult
        """
        return self._request(_CURRENT_PACK_HIERARCHY.bind(companyId=company_id), json=data)

    def pack_inventories(
        self, company_id: str, *, data: list[PackInventoryItemModelInput] | list[dict]
    ) -> SuggestedCombinedHandlingUnitListServiceResponseResult:
        """POST /company/{companyId}/pack/inventories.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/pack_inventories.html
        Request model: List[PackInventoryItemModelInput]
        Response model: SuggestedCombinedHandlingUnitListServiceResponseResult
        """
        return self._request(_CURRENT_PACK_INVENTORIES.bind(companyId=company_id), json=data)

    def get_handling_unit_materials(
        self, company_id: str, *, data: GetHandlingUnitMaterialsModelInput | dict
    ) -> HandlingUnitMaterialsResponseServiceResponseResult:
        """POST /company/{companyId}/pack/handlingunit/materials.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/get_handling_unit_materials.html
        Request model: GetHandlingUnitMaterialsModelInput
        Response model: HandlingUnitMaterialsResponseServiceResponseResult
        """
        return self._request(_CURRENT_GET_HANDLING_UNIT_MATERIALS.bind(companyId=company_id), json=data)

    def validate_handling_unit(
        self, company_id: str, *, data: ValidateHandlingUnitModelInput | dict
    ) -> ValidateHandlingUnitResultResult:
        """POST /company/{companyId}/pack/validate.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/validate_handling_unit.html
        Request model: ValidateHandlingUnitModelInput
        Response model: ValidateHandlingUnitResultResult
        """
        return self._request(_CURRENT_VALIDATE_HANDLING_UNIT.bind(companyId=company_id), json=data)

    def pack_handling_units(
        self, company_id: str, *, data: PackHandlingUnitsModelInput | dict
    ) -> JobHandlingUnitListServiceResponseResult:
        """POST /company/{companyId}/pack/handling-units.

        Uses explicit 8_01 identifiers and validates the complete request.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/companies/pack_handling_units.html
        Request model: PackHandlingUnitsModelInput
        Response model: JobHandlingUnitListServiceResponseResult
        """
        return self._request(_CURRENT_PACK_HANDLING_UNITS.bind(companyId=company_id), json=data)
