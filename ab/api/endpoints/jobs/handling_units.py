"""Typed 8_01 handling units operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

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
    JobHandlingUnitModel,
    ManageableJobHandlingUnitModel,
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

# Flag -> the field whose change turns it on (a deliberate choice, as in the portal).
_CHOICE_FLAGS = {"is_container_changed": "container_type_id", "is_fill_changed": "fill_id"}
_MISSING = object()


def _given(unit: dict[str, Any], name: str, alias: str) -> Any:
    """Value the caller gave for a field, under its Python name or wire alias."""
    if name in unit:
        return unit[name]
    return unit.get(alias, _MISSING)


def _as_request(value: Any, model: type[BaseModel] | None) -> Any:
    """Shape a value read from the server the way *model* expects it in a request."""
    if model is None or not isinstance(value, list):
        return value
    rows = []
    for item in value:
        row = {}
        for name, field in model.model_fields.items():
            stored = getattr(item, name, None)
            if stored is not None:
                row[field.alias or name] = stored
        rows.append(row)
    return rows


def _row_model(annotation: Any) -> type[BaseModel] | None:
    """The request model of a ``list[Model]`` field, if it is one."""
    for arg in getattr(annotation, "__args__", ()):
        if isinstance(arg, type) and issubclass(arg, BaseModel):
            return arg
        nested = _row_model(arg)
        if nested is not None:
            return nested
    return None


def _complete_from_current(
    unit: dict[str, Any], current: JobHandlingUnitDetails | None, model: type[BaseModel]
) -> dict[str, Any]:
    """Complete a write to an existing handling unit: what the caller left out stays as it is.

    The server overwrites the whole unit with the request: an omitted scalar becomes
    null, an omitted flag ``false``, an omitted collection empty. A caller who does
    not mention a field means "leave it", so every field of *model* the caller left
    out is taken from the unit as it stands. Two refinements:

    - ``is_container_changed`` / ``is_fill_changed`` become ``True`` when the request
      names a container type / fill different from the stored one, and otherwise keep
      their stored value.
    - Explicit values, including ``None`` and ``[]``, always win.

    Anything that cannot be inferred -- an unknown unit, a server that does not report
    a required flag -- is left out, and request validation reports it as missing.
    """
    if current is None:
        return unit
    out = dict(unit)
    for name, field in model.model_fields.items():
        alias = field.alias or name
        if _given(out, name, alias) is not _MISSING:
            continue
        stored = getattr(current, name, None)
        if stored is None:
            continue
        source = _CHOICE_FLAGS.get(name)
        if source is not None:
            requested = _given(out, source, model.model_fields[source].alias or source)
            if requested is not _MISSING and requested != getattr(current, source):
                stored = True
        out[alias] = _as_request(stored, _row_model(field.annotation))
    return out


def _is_complete(unit: dict[str, Any], model: type[BaseModel]) -> bool:
    """Whether the caller named every field, so nothing is left to read from the server."""
    return all(_given(unit, name, field.alias or name) is not _MISSING for name, field in model.model_fields.items())


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

        ``is_locked``, ``is_container_changed`` and ``is_fill_changed`` are required:
        a new unit has no stored state to take them from.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.create.html
        Request model: AddJobHandlingUnitModel
        Response model: JobHandlingUnit
        """
        return self._request(_CREATE.bind(jobDisplayId=job_display_id), json=kwargs)

    def manage(
        self, job_display_id: int, *, delete_omitted: bool = False, **kwargs: Any
    ) -> ManageHandlingUnitsResponse:
        """``POST /job/{jobDisplayId}/handlingUnit/manage`` — replaces the job's handling-unit arrangement.

        ``handling_units`` is the **whole job's** arrangement, not a patch:

        - A unit of the job that the list leaves out is **deleted** by the server, with
          its nesting, inventory links, materials, documents and shipping contents. The
          SDK refuses that before any write unless ``delete_omitted=True``.
        - A unit with a positive ``id`` is updated. Every field you leave out keeps its
          current value (see below); pass ``None`` or ``[]`` to clear one.
        - A unit with a negative ``id`` is created; use distinct negative IDs and refer
          to them from ``content_handling_units``. ``id`` 0 is rejected. A new unit must
          name ``is_locked``, ``is_container_changed``, ``is_fill_changed`` and
          ``inventory_items``.

        The server overwrites each submitted unit completely, so the SDK first reads the
        job's units (one ``get_all``) and fills in whatever an existing unit's entry
        omits. A ``container_type_id`` or ``fill_id`` different from the stored one turns
        ``is_container_changed`` / ``is_fill_changed`` on.

        Args:
            job_display_id: Job display ID.
            delete_omitted: Allow the server to delete the job's units that
                ``handling_units`` does not list. Defaults to ``False``.

        Raises:
            ValueError: A listed positive ``id`` is not a unit of the job, or existing
                units would be deleted and ``delete_omitted`` is not set.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.manage.html
        Request model: ManageHandlingUnitsModel
        Response model: ManageHandlingUnitsResponse
        """
        units_key = "handling_units" if "handling_units" in kwargs else "handlingUnits"
        units = kwargs.get(units_key)
        if units is not None:
            units = [u.model_dump(by_alias=True, exclude_unset=True) if isinstance(u, BaseModel) else u for u in units]
            current = {unit.id: unit for unit in self.get_all(job_display_id) if unit.id is not None}
            listed = {u.get("id") for u in units if isinstance(u.get("id"), int) and u["id"] > 0}
            unknown = sorted(listed - current.keys())
            if unknown:
                raise ValueError(
                    f"jobs.handling_units.manage: unit ID(s) {unknown} are not handling units of job "
                    f"{job_display_id}. Use a negative id for a new unit."
                )
            omitted = sorted(current.keys() - listed)
            if omitted and not delete_omitted:
                raise ValueError(
                    f"jobs.handling_units.manage replaces the whole job's arrangement: unit ID(s) {omitted} "
                    f"of job {job_display_id} are not listed and would be deleted. List them to keep them, "
                    "or pass delete_omitted=True to delete them."
                )
            kwargs = {
                **kwargs,
                units_key: [
                    _complete_from_current(u, current.get(u.get("id")), ManageableJobHandlingUnitModel) for u in units
                ],
            }
        return self._request(_MANAGE.bind(jobDisplayId=job_display_id), json=kwargs)

    def update(self, job_display_id: int, handling_unit_id: int, **kwargs: Any) -> None:
        """``PUT /job/{jobDisplayId}/handlingUnit/{id}``

        The server overwrites the unit with the request. Every field you leave out
        keeps its current value, read with one ``get_all`` (skipped when you name every
        field); pass ``None`` to clear one. A ``container_type_id`` or ``fill_id``
        different from the stored one turns ``is_container_changed`` /
        ``is_fill_changed`` on.

        Docs: https://ab-sdk.readthedocs.io/en/latest/api/jobs/handling_units.update.html
        Request model: JobHandlingUnitModel
        """
        if not _is_complete(kwargs, JobHandlingUnitModel):
            current = next((u for u in self.get_all(job_display_id) if u.id == handling_unit_id), None)
            kwargs = _complete_from_current(kwargs, current, JobHandlingUnitModel)
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
