"""Live 8_01 packing validation on an explicitly selected disposable staging job.

Creates its own inventory and handling units, checks persisted relationships,
then deletes only the records it created. Optional multi-shipment reads inspect
all records without booking or cancelling a carrier shipment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ab import ABConnectAPI
from ab.api.models.packing import JobHandlingUnitModel, JobInventoryItemModel
from examples._capture import save


def dump(records):
    return [r.model_dump(mode="json", by_alias=True) for r in records]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=int, required=True)
    parser.add_argument("--shipping-job", type=int)
    args = parser.parse_args()
    api = ABConnectAPI(env="staging")
    assert api._settings.environment == "staging"
    job = args.job
    before_inventory = api.jobs.inventory.get_all(job)
    before_units = api.jobs.handling_units.get_all(job)
    # Keep this test confined to a job with no existing packing arrangement.
    if before_inventory or before_units:
        raise ValueError("Choose an empty estimate for this isolated packing test")
    inventory_ids, unit_ids = [], []
    checks = []

    def passed(name):
        checks.append(name)
        print(json.dumps({"check": name, "result": "passed", "job": job}), flush=True)

    try:
        item_body = dict(
            quantity=2,
            is_active=True,
            sequence_no=1,
            name="SDK 8_01 validation",
            length=12,
            width=10,
            height=8,
            weight=4,
            value=125.5,
        )
        item = api.jobs.inventory.create(job, **item_body)
        inventory_ids.append(item.id)
        assert item.id and item.quantity == 2
        save("JobInventoryItem.json", item)
        persisted = api.jobs.inventory.get_all(job)
        assert len(persisted) == 1 and persisted[0].id == item.id
        passed("inventory_create_read")
        item_body.update(value=150.5, parent_inventory_item_id=None)
        api.jobs.inventory.update(job, item.id, **item_body)
        persisted = api.jobs.inventory.get_all(job)
        assert persisted[0].value == 150.5 and persisted[0].parent_inventory_item_id is None
        save("JobInventoryItemModel.json", JobInventoryItemModel(**item_body))
        passed("inventory_update_nullable_clear")

        unit_body = dict(
            quantity=1,
            is_active=True,
            sequence_no=0,
            name="SDK 8_01 unit",
            length=14,
            width=12,
            height=10,
            weight=6,
            declared_value=150.5,
        )
        unit = api.jobs.handling_units.create(job, **unit_body)
        unit_ids.append(unit.id)
        assert unit.id
        save("JobHandlingUnit.json", unit)
        api.jobs.handling_units.add_inventory(job, unit.id, data=[{"id": item.id, "count": 2}])
        units = api.jobs.handling_units.get_all(job)
        assert units[0].inventory_items[0].id == item.id and units[0].inventory_items[0].count == 2
        save("JobHandlingUnitDetails.json", units[0])
        passed("handling_unit_create_inventory_association")
        api.jobs.handling_units.update_inventory(job, unit.id, item.id, count=1)
        units = api.jobs.handling_units.get_all(job)
        assert units[0].inventory_items[0].count == 1
        passed("inventory_association_update")
        unit_body.update(weight=7)
        api.jobs.handling_units.update(job, unit.id, **unit_body)
        units = api.jobs.handling_units.get_all(job)
        assert units[0].weight == 7 and units[0].inventory_items[0].id == item.id
        save("JobHandlingUnitModel.json", JobHandlingUnitModel(**unit_body))
        passed("handling_unit_update_preserves_contents")
        api.jobs.handling_units.delete_inventory(job, unit.id, item.id)
        assert not api.jobs.handling_units.get_all(job)[0].inventory_items
        passed("inventory_association_delete")

        child = api.jobs.handling_units.create(job, **{**unit_body, "sequence_no": 1})
        unit_ids.append(child.id)
        api.jobs.handling_units.add_content_units(job, unit.id, data=[{"id": child.id, "count": 1}])
        parent = next(u for u in api.jobs.handling_units.get_all(job) if u.id == unit.id)
        assert parent.content_handling_units[0].id == child.id
        api.jobs.handling_units.update_content_unit(job, unit.id, child.id, count=1)
        parent = next(u for u in api.jobs.handling_units.get_all(job) if u.id == unit.id)
        assert parent.content_handling_units[0].count == 1
        api.jobs.handling_units.delete_content_unit(job, unit.id, child.id)
        parent = next(u for u in api.jobs.handling_units.get_all(job) if u.id == unit.id)
        assert not parent.content_handling_units
        passed("nested_handling_unit_add_update_delete")
        assert api.jobs.handling_units.get_materials(job, unit.id) == []
        api.jobs.handling_units.set_container_material(job, unit.id, container_handling_unit_material_id=None)
        passed("empty_material_read_and_container_clear")
    finally:
        for unit_id in reversed(unit_ids):
            api.jobs.handling_units.delete(job, unit_id)
        for item_id in reversed(inventory_ids):
            api.jobs.inventory.delete(job, item_id)
        assert dump(api.jobs.inventory.get_all(job)) == dump(before_inventory)
        assert dump(api.jobs.handling_units.get_all(job)) == dump(before_units)
        passed("cleanup_restores_original_collections")

    if args.shipping_job:
        shippings = api.jobs.shippings.get_all(args.shipping_job)
        active = [s for s in shippings if s.is_archived is False]
        assert len(active) >= 2, "Expected at least two active shipping records"
        for shipping in active:
            save("Shipping.json", shipping)
            export = api.jobs.shipment.get_shipping_export_data(args.shipping_job, shipping.id)
            if export is not None:
                export.to_request()
                save("ShippingExportData.json", export)
            print(
                json.dumps(
                    {
                        "check": "explicit_shipping_export_read",
                        "job": args.shipping_job,
                        "shipping_id": shipping.id,
                        "has_export": export is not None,
                    }
                ),
                flush=True,
            )
        assert dump(api.jobs.shippings.get_all(args.shipping_job)) == dump(shippings)
        print(
            json.dumps(
                {
                    "check": "multiple_active_shipping_reads_preserve_collection",
                    "result": "passed",
                    "job": args.shipping_job,
                    "active_count": len(active),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
