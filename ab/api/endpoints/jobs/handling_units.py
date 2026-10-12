"""Typed 8_01 handling units operations."""

from __future__ import annotations

from typing import Any

from ab.api.base import BaseEndpoint
from ab.api.models.packing import (
    AddContentHandlingUnitModel,
    AddInventoryModel,
    ContentHandlingUnit,
    ContentInventoryItem,
    HandlingUnitMaterial,
    HandlingUnitMaterialModel,
    JobHandlingUnit,
    JobHandlingUnitDetails,
    ManageHandlingUnitsResponse,
)
from ab.api.route import Route

_GET_ALL = Route("GET", "/job/{jobDisplayId}/handlingUnit", response_model="List[JobHandlingUnitDetails]")
_CREATE = Route(
    "POST",
    "/job/{jobDisplayId}/handlingUnit",
    request_model="AddJobHandlingUnitModel",
    response_model="JobHandlingUnit",
)
_MANAGE = Route(
    "POST",
    "/job/{jobDisplayId}/handlingUnit/manage",
    request_model="ManageHandlingUnitsModel",
    response_model="ManageHandlingUnitsResponse",
)
_UPDATE = Route("PUT", "/job/{jobDisplayId}/handlingUnit/{id}", request_model="JobHandlingUnitModel")
_DELETE = Route("DELETE", "/job/{jobDisplayId}/handlingUnit/{id}")
_ADD_INVENTORY = Route(
    "POST",
    "/job/{jobDisplayId}/handlingUnit/{id}/inventory",
    request_model="List[AddInventoryModel]",
    response_model="List[ContentInventoryItem]",
)
_UPDATE_INVENTORY = Route(
    "PUT", "/job/{jobDisplayId}/handlingUnit/{id}/inventory/{inventoryItemId}", request_model="InventoryModel"
)
_DELETE_INVENTORY = Route("DELETE", "/job/{jobDisplayId}/handlingUnit/{id}/inventory/{inventoryItemId}")
_ADD_CONTENT_UNITS = Route(
    "POST",
    "/job/{jobDisplayId}/handlingUnit/{id}/contentUnit",
    request_model="List[AddContentHandlingUnitModel]",
    response_model="List[ContentHandlingUnit]",
)
_UPDATE_CONTENT_UNIT = Route(
    "PUT", "/job/{jobDisplayId}/handlingUnit/{id}/contentUnit/{contentUnitId}", request_model="ContentHandlingUnitModel"
)
_DELETE_CONTENT_UNIT = Route("DELETE", "/job/{jobDisplayId}/handlingUnit/{id}/contentUnit/{contentUnitId}")
_GET_MATERIALS = Route(
    "GET", "/job/{jobDisplayId}/handlingUnit/{id}/materials", response_model="List[HandlingUnitMaterial]"
)
_ADD_MATERIALS = Route(
    "POST",
    "/job/{jobDisplayId}/handlingUnit/{id}/materials",
    request_model="List[HandlingUnitMaterialModel]",
    response_model="List[HandlingUnitMaterial]",
)
_REPLACE_MATERIALS = Route(
    "PUT",
    "/job/{jobDisplayId}/handlingUnit/{id}/materials",
    request_model="List[HandlingUnitMaterialModel]",
    response_model="List[HandlingUnitMaterial]",
)
_SET_CONTAINER_MATERIAL = Route(
    "PUT",
    "/job/{jobDisplayId}/handlingUnit/{id}/container-material",
    request_model="SetHandlingUnitContainerMaterialModel",
)
_UPDATE_MATERIAL = Route(
    "PATCH", "/job/{jobDisplayId}/handlingUnit/{id}/materials/{materialId}", request_model="HandlingUnitMaterialModel"
)
_DELETE_MATERIAL = Route("DELETE", "/job/{jobDisplayId}/handlingUnit/{id}/materials/{materialId}")


class JobHandlingUnitsEndpoint(BaseEndpoint):
    """Job handling units operations; identifiers are scoped to the job."""

    def get_all(self, job_display_id: int) -> list[JobHandlingUnitDetails]:
        """``GET /job/{jobDisplayId}/handlingUnit``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.get_all.html
        Response model: List[JobHandlingUnitDetails]
        """
        return self._request(_GET_ALL.bind(jobDisplayId=job_display_id))

    def create(self, job_display_id: int, **kwargs: Any) -> JobHandlingUnit:
        """``POST /job/{jobDisplayId}/handlingUnit``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.create.html
        Request model: AddJobHandlingUnitModel
        Response model: JobHandlingUnit
        """
        return self._request(_CREATE.bind(jobDisplayId=job_display_id), json=kwargs)

    def manage(self, job_display_id: int, **kwargs: Any) -> ManageHandlingUnitsResponse:
        """``POST /job/{jobDisplayId}/handlingUnit/manage`` — submits the complete handling-unit arrangement.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.manage.html
        Request model: ManageHandlingUnitsModel
        Response model: ManageHandlingUnitsResponse
        """
        return self._request(_MANAGE.bind(jobDisplayId=job_display_id), json=kwargs)

    def update(self, job_display_id: int, handling_unit_id: int, **kwargs: Any) -> None:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.update.html
        Request model: JobHandlingUnitModel
        """
        return self._request(_UPDATE.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=kwargs)

    def delete(self, job_display_id: int, handling_unit_id: int) -> None:
        """``DELETE /job/{jobDisplayId}/handlingUnit/{id}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.delete.html
        """
        return self._request(_DELETE.bind(jobDisplayId=job_display_id, id=handling_unit_id))

    def add_inventory(
        self, job_display_id: int, handling_unit_id: int, *, data: list[AddInventoryModel]
    ) -> list[ContentInventoryItem]:
        """``POST /job/{jobDisplayId}/handlingUnit/{id}/inventory``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.add_inventory.html
        Request model: List[AddInventoryModel]
        Response model: List[ContentInventoryItem]
        """
        return self._request(_ADD_INVENTORY.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=data)

    def update_inventory(
        self, job_display_id: int, handling_unit_id: int, inventory_item_id: int, **kwargs: Any
    ) -> None:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}/inventory/{inventoryItemId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.update_inventory.html
        Request model: InventoryModel
        """
        return self._request(
            _UPDATE_INVENTORY.bind(jobDisplayId=job_display_id, id=handling_unit_id, inventoryItemId=inventory_item_id),
            json=kwargs,
        )

    def delete_inventory(self, job_display_id: int, handling_unit_id: int, inventory_item_id: int) -> None:
        """``DELETE /job/{jobDisplayId}/handlingUnit/{id}/inventory/{inventoryItemId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.delete_inventory.html
        """
        return self._request(
            _DELETE_INVENTORY.bind(jobDisplayId=job_display_id, id=handling_unit_id, inventoryItemId=inventory_item_id)
        )

    def add_content_units(
        self, job_display_id: int, handling_unit_id: int, *, data: list[AddContentHandlingUnitModel]
    ) -> list[ContentHandlingUnit]:
        """``POST /job/{jobDisplayId}/handlingUnit/{id}/contentUnit``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.add_content_units.html
        Request model: List[AddContentHandlingUnitModel]
        Response model: List[ContentHandlingUnit]
        """
        return self._request(_ADD_CONTENT_UNITS.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=data)

    def update_content_unit(
        self, job_display_id: int, handling_unit_id: int, content_unit_id: int, **kwargs: Any
    ) -> None:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}/contentUnit/{contentUnitId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.update_content_unit.html
        Request model: ContentHandlingUnitModel
        """
        return self._request(
            _UPDATE_CONTENT_UNIT.bind(jobDisplayId=job_display_id, id=handling_unit_id, contentUnitId=content_unit_id),
            json=kwargs,
        )

    def delete_content_unit(self, job_display_id: int, handling_unit_id: int, content_unit_id: int) -> None:
        """``DELETE /job/{jobDisplayId}/handlingUnit/{id}/contentUnit/{contentUnitId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.delete_content_unit.html
        """
        return self._request(
            _DELETE_CONTENT_UNIT.bind(jobDisplayId=job_display_id, id=handling_unit_id, contentUnitId=content_unit_id)
        )

    def get_materials(self, job_display_id: int, handling_unit_id: int) -> list[HandlingUnitMaterial]:
        """``GET /job/{jobDisplayId}/handlingUnit/{id}/materials``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.get_materials.html
        Response model: List[HandlingUnitMaterial]
        """
        return self._request(_GET_MATERIALS.bind(jobDisplayId=job_display_id, id=handling_unit_id))

    def add_materials(
        self, job_display_id: int, handling_unit_id: int, *, data: list[HandlingUnitMaterialModel]
    ) -> list[HandlingUnitMaterial]:
        """``POST /job/{jobDisplayId}/handlingUnit/{id}/materials``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.add_materials.html
        Request model: List[HandlingUnitMaterialModel]
        Response model: List[HandlingUnitMaterial]
        """
        return self._request(_ADD_MATERIALS.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=data)

    def replace_materials(
        self, job_display_id: int, handling_unit_id: int, *, data: list[HandlingUnitMaterialModel]
    ) -> list[HandlingUnitMaterial]:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}/materials`` — replaces the complete material list.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.replace_materials.html
        Request model: List[HandlingUnitMaterialModel]
        Response model: List[HandlingUnitMaterial]
        """
        return self._request(_REPLACE_MATERIALS.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=data)

    def set_container_material(self, job_display_id: int, handling_unit_id: int, **kwargs: Any) -> None:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}/container-material``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.set_container_material.html
        Request model: SetHandlingUnitContainerMaterialModel
        """
        return self._request(
            _SET_CONTAINER_MATERIAL.bind(jobDisplayId=job_display_id, id=handling_unit_id), json=kwargs
        )

    def update_material(self, job_display_id: int, handling_unit_id: int, material_id: int, **kwargs: Any) -> None:
        """``PATCH /job/{jobDisplayId}/handlingUnit/{id}/materials/{materialId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.update_material.html
        Request model: HandlingUnitMaterialModel
        """
        return self._request(
            _UPDATE_MATERIAL.bind(jobDisplayId=job_display_id, id=handling_unit_id, materialId=material_id), json=kwargs
        )

    def delete_material(self, job_display_id: int, handling_unit_id: int, material_id: int) -> None:
        """``DELETE /job/{jobDisplayId}/handlingUnit/{id}/materials/{materialId}``

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.delete_material.html
        """
        return self._request(
            _DELETE_MATERIAL.bind(jobDisplayId=job_display_id, id=handling_unit_id, materialId=material_id)
        )
