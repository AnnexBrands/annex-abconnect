"""Synthetic contract tests: no payload here is a captured API fixture."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ab.api.endpoints.jobs.handling_units import JobHandlingUnitsEndpoint
from ab.api.endpoints.jobs.inventory import JobInventoryEndpoint
from ab.api.endpoints.jobs.shippings import JobShippingsEndpoint
from ab.api.models.packing import AddJobHandlingUnitModel, JobInventoryItemModel


@pytest.mark.parametrize("model,min_sequence", [(JobInventoryItemModel, 1), (AddJobHandlingUnitModel, 0)])
def test_required_fields_ranges_and_unknown_fields(model, min_sequence):
    valid = {"quantity": 1, "isActive": True, "sequenceNo": min_sequence}
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
