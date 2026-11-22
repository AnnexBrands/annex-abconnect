"""Synthetic contract tests: no payload here is a captured API fixture."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ab.api.endpoints.jobs.handling_units import JobHandlingUnitsEndpoint
from ab.api.endpoints.jobs.inventory import JobInventoryEndpoint
from ab.api.endpoints.jobs.shippings import JobShippingsEndpoint
from ab.api.models.packing import AddJobHandlingUnitModel, JobInventoryItemModel

_FLAGS = {"isContainerChanged": False, "isFillChanged": False, "isLocked": False}


@pytest.mark.parametrize(
    "model,min_sequence,extra", [(JobInventoryItemModel, 1, {}), (AddJobHandlingUnitModel, 0, _FLAGS)]
)
def test_required_fields_ranges_and_unknown_fields(model, min_sequence, extra):
    valid = {"quantity": 1, "isActive": True, "sequenceNo": min_sequence, **extra}
    assert model.check(valid) == valid
    for field, value in [("quantity", 0), ("sequenceNo", min_sequence - 1), ("length", -1), ("typo", 5)]:
        with pytest.raises(ValidationError):
            model.check({**valid, field: value})
    for field in valid:
        with pytest.raises(ValidationError):
            model.check({k: v for k, v in valid.items() if k != field})


def test_inventory_update_preserves_explicit_clears_and_only_targets_one_record():
    client = MagicMock()
    client.request.return_value = None
    JobInventoryEndpoint(client).update(
        123,
        7,
        quantity=2,
        is_active=True,
        sequence_no=1,
        parent_inventory_item_id=None,
        value=125.5,
        customer_item_id="synthetic-ref",
    )
    client.request.assert_called_once_with(
        "PUT",
        "/job/123/inventory/7",
        json={
            "quantity": 2,
            "isActive": True,
            "sequenceNo": 1,
            "parentInventoryItemId": None,
            "value": 125.5,
            "customerItemId": "synthetic-ref",
        },
    )


def test_handling_unit_create_preserves_inventory_and_nested_units():
    client = MagicMock()
    client.request.return_value = {
        "id": 20,
        "inventoryItems": [{"id": 7, "count": 2}],
        "contentHandlingUnits": [{"id": 19, "count": 1}],
    }
    result = JobHandlingUnitsEndpoint(client).create(
        123,
        quantity=1,
        is_active=True,
        sequence_no=0,
        is_locked=False,
        is_container_changed=False,
        is_fill_changed=False,
        inventory_items=[{"id": 7, "count": 2}],
        content_handling_units=[{"id": 19, "count": 1}],
    )
    assert result.inventory_items[0].id == 7
    assert result.content_handling_units[0].id == 19
    assert client.request.call_args.kwargs["json"]["inventoryItems"] == [{"id": 7, "count": 2}]
    assert client.request.call_count == 1


def test_invalid_nested_inventory_prevents_any_http_request():
    client = MagicMock()
    with pytest.raises(ValidationError):
        JobHandlingUnitsEndpoint(client).add_inventory(123, 20, data=[{"id": 7, "count": -1}])
    client.request.assert_not_called()


def test_material_array_and_container_clear_keep_transport_shape():
    client = MagicMock()
    client.request.return_value = None
    endpoint = JobHandlingUnitsEndpoint(client)
    endpoint.add_materials(123, 20, data=[{"materialId": 10, "quantityPlanned": 2, "unitCost": 3.5}])
    client.request.assert_called_once_with(
        "POST",
        "/job/123/handlingUnit/20/materials",
        json=[{"materialId": 10, "quantityPlanned": 2, "unitCost": 3.5}],
    )
    client.reset_mock()
    endpoint.set_container_material(123, 20, container_handling_unit_material_id=None)
    client.request.assert_called_once_with(
        "PUT",
        "/job/123/handlingUnit/20/container-material",
        json={"containerHandlingUnitMaterialId": None},
    )


def test_shippings_keeps_multiple_active_and_archived_records_and_quote_relationships():
    client = MagicMock()
    quote = "11111111-2222-4333-8444-555555555555"
    client.request.return_value = [
        {"id": 1, "isArchived": False, "freightQuoteOptions": [quote], "handlingUnits": [{"id": 20, "quantity": 1}]},
        {"id": 2, "isArchived": False, "freightQuoteOptions": [], "handlingUnits": []},
        {"id": 3, "isArchived": True, "freightQuoteOptions": [], "handlingUnits": []},
    ]
    result = JobShippingsEndpoint(client).get_all(123)
    assert [s.id for s in result] == [1, 2, 3]
    assert str(result[0].freight_quote_options[0]) == quote
    assert result[0].handling_units[0].id == 20
    assert result[2].is_archived is True


def test_array_endpoint_rejects_single_object_before_http():
    client = MagicMock()
    with pytest.raises(TypeError, match="JSON array"):
        JobHandlingUnitsEndpoint(client).add_inventory(123, 20, data={"id": 7, "count": 1})
    client.request.assert_not_called()


# --- handling-unit state the server overwrites on every write -----------------

_STORED = {
    "id": 20,
    "quantity": 1,
    "isActive": True,
    "sequenceNo": 0,
    "containerTypeId": 5,
    "fillId": 3,
    "isLocked": True,
    "isContainerChanged": False,
    "isFillChanged": True,
    "inventoryItems": [{"id": 7, "count": 2}],
}
_BASE = {"quantity": 1, "is_active": True, "sequence_no": 0}


def _client(*, write_response=None, stored=_STORED):
    client = MagicMock()
    client.request.side_effect = lambda method, path, **kw: [stored] if method == "GET" else write_response
    return client


def _written(client):
    return next(c for c in client.request.call_args_list if c.args[0] != "GET").kwargs["json"]


def test_create_requires_all_three_state_flags_before_http():
    client = MagicMock()
    with pytest.raises(ValidationError, match="isLocked"):
        JobHandlingUnitsEndpoint(client).create(123, **_BASE, is_container_changed=False, is_fill_changed=False)
    client.request.assert_not_called()


def test_update_keeps_stored_flags_when_the_caller_names_none():
    client = _client()
    JobHandlingUnitsEndpoint(client).update(123, 20, **_BASE, container_type_id=5, fill_id=3)
    body = _written(client)
    assert (body["isLocked"], body["isContainerChanged"], body["isFillChanged"]) == (True, False, True)
    assert [c.args[:2] for c in client.request.call_args_list] == [
        ("GET", "/job/123/handlingUnit"),
        ("PUT", "/job/123/handlingUnit/20"),
    ]


def test_update_turns_a_flag_on_when_container_or_fill_differs_from_stored():
    client = _client(stored={**_STORED, "isFillChanged": False})
    JobHandlingUnitsEndpoint(client).update(123, 20, **_BASE, container_type_id=9, fill_id=4)
    body = _written(client)
    assert (body["isContainerChanged"], body["isFillChanged"], body["isLocked"]) == (True, True, True)


def test_explicit_values_win_over_stored_state():
    client = _client()
    JobHandlingUnitsEndpoint(client).update(
        123, 20, **_BASE, fill_id=4, is_locked=False, is_container_changed=True, is_fill_changed=False
    )
    body = _written(client)
    assert (body["isLocked"], body["isContainerChanged"], body["isFillChanged"]) == (False, True, False)


def test_update_keeps_every_omitted_field_and_clears_only_explicit_nulls():
    stored = {**_STORED, "length": 10.0, "width": 8.0, "weight": 5.5, "name": "synthetic"}
    client = _client(stored=stored)
    JobHandlingUnitsEndpoint(client).update(123, 20, weight=6.0, name=None)
    body = _written(client)
    assert (body["quantity"], body["isActive"], body["sequenceNo"]) == (1, True, 0)
    assert (body["length"], body["width"], body["weight"], body["name"]) == (10.0, 8.0, 6.0, None)
    assert (body["containerTypeId"], body["fillId"]) == (5, 3)
    assert "inventoryItems" not in body and "id" not in body


def test_update_skips_the_read_when_every_field_is_named():
    from ab.api.models.packing import JobHandlingUnitModel

    client = _client()
    everything = {name: None for name in JobHandlingUnitModel.model_fields}
    everything.update(_BASE, has_custom_name=False, is_locked=False, is_container_changed=False, is_fill_changed=False)
    JobHandlingUnitsEndpoint(client).update(123, 20, **everything)
    assert [c.args[0] for c in client.request.call_args_list] == ["PUT"]


@pytest.mark.parametrize(
    "stored",
    [
        {**_STORED, "id": 99},  # the unit is not on the job
        {k: v for k, v in _STORED.items() if not k.startswith("is") or k == "isActive"},  # server omits the flags
    ],
)
def test_update_fails_locally_when_flags_cannot_be_inferred(stored):
    client = _client(stored=stored)
    with pytest.raises(ValidationError, match="isLocked"):
        JobHandlingUnitsEndpoint(client).update(123, 20, **_BASE)
    assert all(c.args[0] == "GET" for c in client.request.call_args_list)


def test_manage_preserves_inventory_and_flags_of_existing_units():
    client = _client(write_response={"success": True, "handlingUnits": []})
    JobHandlingUnitsEndpoint(client).manage(123, handling_units=[{"id": 20, **_BASE}])
    unit = _written(client)["handlingUnits"][0]
    assert unit["inventoryItems"] == [{"id": 7, "count": 2}]
    assert (unit["isLocked"], unit["isContainerChanged"], unit["isFillChanged"]) == (True, False, True)


def test_manage_sends_an_explicit_empty_inventory_as_given():
    client = _client(write_response={"success": True, "handlingUnits": []})
    JobHandlingUnitsEndpoint(client).manage(
        123, handling_units=[{"id": 20, **_BASE, "inventory_items": [], "is_locked": False}]
    )
    unit = _written(client)["handlingUnits"][0]
    assert unit["inventoryItems"] == []
    assert unit["isLocked"] is False


def test_manage_requires_full_state_for_new_units_before_any_write():
    client = _client(stored={**_STORED})
    endpoint = JobHandlingUnitsEndpoint(client)
    keep = {"id": 20}
    with pytest.raises(ValidationError, match="inventoryItems"):
        endpoint.manage(123, handling_units=[keep, {"id": -1, **_BASE, **_FLAGS}])
    assert all(c.args[0] == "GET" for c in client.request.call_args_list)
    endpoint.manage(123, handling_units=[keep, {"id": -1, **_BASE, **_FLAGS, "inventoryItems": []}])
    assert [u["id"] for u in _written(client)["handlingUnits"]] == [20, -1]


def test_manage_refuses_to_delete_unlisted_units_unless_told_to():
    client = _client(write_response={"success": True, "handlingUnits": []})
    endpoint = JobHandlingUnitsEndpoint(client)
    new = {"id": -1, **_BASE, **_FLAGS, "inventoryItems": []}
    with pytest.raises(ValueError, match=r"\[20\].*would be deleted"):
        endpoint.manage(123, handling_units=[new])
    assert all(c.args[0] == "GET" for c in client.request.call_args_list)
    endpoint.manage(123, handling_units=[new], delete_omitted=True)
    assert [u["id"] for u in _written(client)["handlingUnits"]] == [-1]


@pytest.mark.parametrize("named", [[], [99], [20, 99]])
def test_manage_refuses_when_the_named_deletions_are_not_exactly_the_omitted_units(named):
    client = _client(write_response={"success": True, "handlingUnits": []})
    new = {"id": -1, **_BASE, **_FLAGS, "inventoryItems": []}
    with pytest.raises(ValueError, match="would be deleted"):
        JobHandlingUnitsEndpoint(client).manage(123, handling_units=[new], delete_omitted=named)
    assert all(c.args[0] == "GET" for c in client.request.call_args_list)


def test_manage_deletes_exactly_the_named_units_and_rejects_names_when_nothing_is_omitted():
    client = _client(write_response={"success": True, "handlingUnits": []})
    endpoint = JobHandlingUnitsEndpoint(client)
    new = {"id": -1, **_BASE, **_FLAGS, "inventoryItems": []}
    endpoint.manage(123, handling_units=[new], delete_omitted={20})
    assert [u["id"] for u in _written(client)["handlingUnits"]] == [-1]
    client.reset_mock()
    with pytest.raises(ValueError, match=r"delete_omitted names \[20\]"):
        endpoint.manage(123, handling_units=[{"id": 20}], delete_omitted=[20])
    endpoint.manage(123, handling_units=[{"id": 20}], delete_omitted=[])


def test_manage_rejects_unknown_and_zero_ids_and_a_missing_list_before_any_write():
    client = _client()
    endpoint = JobHandlingUnitsEndpoint(client)
    with pytest.raises(ValueError, match="not handling units of job 123"):
        endpoint.manage(123, handling_units=[{"id": 20}, {"id": 99, **_BASE}])
    with pytest.raises(ValidationError, match="id 0 is not valid"):
        endpoint.manage(123, handling_units=[{"id": 20}, {"id": 0, **_BASE, **_FLAGS, "inventoryItems": []}])
    with pytest.raises(ValidationError, match="handlingUnits"):
        endpoint.manage(123, force_update=False)
    assert all(c.args[0] == "GET" for c in client.request.call_args_list)


def test_manage_keeps_nested_units_materials_and_scalars_of_an_existing_unit():
    stored = {
        **_STORED,
        "length": 12.0,
        "containerHandlingUnitMaterialId": 44,
        "contentHandlingUnits": [{"id": 19, "count": 1}],
        "materials": [
            {"id": 44, "materialId": 10, "quantityPlanned": 2.0, "unitCost": 3.5, "materialName": "synthetic"}
        ],
    }
    client = _client(write_response={"success": True, "handlingUnits": []}, stored=stored)
    JobHandlingUnitsEndpoint(client).manage(123, handling_units=[{"id": 20, "weight": 7.0}])
    unit = _written(client)["handlingUnits"][0]
    assert unit["contentHandlingUnits"] == [{"id": 19, "count": 1}]
    assert unit["materials"] == [{"id": 44, "materialId": 10, "quantityPlanned": 2.0, "unitCost": 3.5}]
    assert (unit["length"], unit["weight"], unit["containerHandlingUnitMaterialId"]) == (12.0, 7.0, 44)


def test_8_01_packing_and_final_quote_additions_round_trip():
    from ab.api.models.release_support import (
        HandlingUnitMaterialsResponseResult,
        PackInventoryItemModelInput,
        SaveFinalQuoteRequest,
        SuggestedHandlingUnitResult,
    )

    item = {"cPackName": "synthetic", "sequenceNo": 1, "quantity": 1}
    requested = {"requestedContainerTypeId": 5, "requestedContainerMaterialId": None, "requestedFillId": 3}
    assert PackInventoryItemModelInput.check({**item, **requested}) == {**item, **requested}
    assert PackInventoryItemModelInput.check(item) == item
    units = {"handlingUnits": [{"id": 20, "quantity": 2}]}
    assert SaveFinalQuoteRequest.check(units) == units
    suggested = SuggestedHandlingUnitResult.model_validate({"containerValidationMessage": "synthetic"})
    assert suggested.container_validation_message == "synthetic" and not suggested.model_extra
    materials = HandlingUnitMaterialsResponseResult.model_validate({"fillRate": 12.5})
    assert materials.fill_rate == 12.5 and not materials.model_extra
