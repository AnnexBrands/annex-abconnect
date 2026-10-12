"""Validate 8_01 against disposable LIVE staging records and propose sanitized captures.

Captures remain in ignored tests/captures pending explicit fixture review.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ab import ABConnectAPI
from ab.progress.certify.session import CertificationSession
from scripts import verify_packing_8_01

COMPANY = "cf8085ed-b2f2-e611-9f52-00155d426802"
JOB = 9165707
SHIPPING_JOB = 13829427
BUNDLE = Path("tests/captures/release_8_01.json")


def dump(value):
    if isinstance(value, list):
        return [dump(v) for v in value]
    return value.model_dump(by_alias=True, mode="json", exclude_unset=True) if hasattr(value, "model_dump") else value


def main():
    api = ABConnectAPI(env="staging")
    assert api._settings.environment == "staging"
    captures = json.loads(BUNDLE.read_text()) if BUNDLE.exists() else {}

    def capture(key, value):
        if value is None:
            return value
        session = CertificationSession(key)
        sample = value[:3] if isinstance(value, list) else value
        session.record_response(sample)
        session.response_payload = dump(sample)
        report = session.propose_fixture()
        captures[session.response_model_name] = {
            "endpoint": key,
            "payload": session.sanitized,
            "review": [d.render() for d in report.review],
        }
        BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        BUNDLE.write_text(json.dumps(captures, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "captured": key,
                    "model": session.response_model_name,
                    "review_count": len(report.review),
                    "extra_fields": list(session.summary.extras),
                }
            ),
            flush=True,
        )
        return value

    mapping = {
        "JobInventoryItem.json": "api.jobs.inventory.create",
        "JobHandlingUnit.json": "api.jobs.handling_units.create",
        "JobHandlingUnitDetails.json": "api.jobs.handling_units.get_all",
        "Shipping.json": "api.jobs.shippings.get_all",
        "ShippingExportData.json": "api.jobs.shipment.get_shipping_export_data",
    }
    verify_packing_8_01.save = lambda name, value: capture(mapping[name], value) if name in mapping else None
    sys.argv = ["verify_packing_8_01", "--job", str(JOB), "--shipping-job", str(SHIPPING_JOB)]
    if os.environ.get("AB_SKIP_PACKING") != "1" and os.environ.get("AB_VALIDATION_PHASE") != "shipping":
        verify_packing_8_01.main()

    if os.environ.get("AB_VALIDATION_PHASE") != "shipping":
        original = dump(api.companies.get_inventory(COMPANY))
        body = dict(
            name="SDK release inventory", is_active=True, is_public=False, length=12, width=10, height=8, weight=4
        )
        item = capture("api.companies.create_inventory", api.companies.create_inventory(COMPANY, data=body))
        try:
            api.companies.update_inventory(
                COMPANY, item.id, data={**body, "value": 125.5, "parentInventoryItemId": None}
            )
            current = api.companies.get_inventory(COMPANY)
            assert next(i for i in current if i.id == item.id).value == 125.5
        finally:
            api.companies.delete_inventory(COMPANY, item.id)
        after = api.companies.get_inventory(COMPANY)
        assert dump([i for i in after if i.id != item.id]) == original
        removed = next((i for i in after if i.id == item.id), None)
        assert removed is None or removed.is_active is False
        print("PASS company_inventory_create_update_delete_restored", flush=True)

        materials = capture("api.companies.get_materials", api.companies.get_materials(COMPANY, only_active=True))
        boxes = capture("api.companies.get_stock_boxes", api.companies.get_stock_boxes(COMPANY))
        capture("api.lookup.get_addons", api.lookup.get_addons())
        capture("api.jobs.add_ons.get_all", api.jobs.add_ons.get_all(JOB))
        unit = api.jobs.handling_units.create(
            JOB,
            quantity=1,
            sequence_no=0,
            is_active=True,
            name="SDK material validation",
            length=14,
            width=12,
            height=10,
            weight=6,
        )
        try:
            material_id = next((m.material_id for m in boxes if m.material_id), None)
            if material_id is None:
                material_id = next(m.nc_material_id for m in materials if m.nc_material_id)
            rows = capture(
                "api.jobs.handling_units.add_materials",
                api.jobs.handling_units.add_materials(
                    JOB, unit.id, data=[{"materialId": material_id, "quantityPlanned": 2, "unitCost": 3.5}]
                ),
            )
            persisted = api.jobs.handling_units.get_materials(JOB, unit.id)
            assert len(persisted) == 1 and persisted[0].quantity_planned == 2
            # Container takes the association ID, not the catalog material ID.
            api.jobs.handling_units.set_container_material(JOB, unit.id, container_handling_unit_material_id=rows[0].id)
            assert api.jobs.handling_units.get_all(JOB)[0].container_handling_unit_material_id == rows[0].id
            api.jobs.handling_units.set_container_material(JOB, unit.id, container_handling_unit_material_id=None)
            api.jobs.handling_units.replace_materials(
                JOB, unit.id, data=[{"materialId": material_id, "quantityPlanned": 3}]
            )
            persisted = api.jobs.handling_units.get_materials(JOB, unit.id)
            assert len(persisted) == 1 and persisted[0].quantity_planned == 3
            api.jobs.handling_units.delete_material(JOB, unit.id, persisted[0].id)
            assert api.jobs.handling_units.get_materials(JOB, unit.id) == []
            print("PASS material_add_replace_container_delete", flush=True)
        finally:
            api.jobs.handling_units.delete(JOB, unit.id)

    before = dump(api.jobs.shippings.get_all(SHIPPING_JOB))
    quotes = capture("api.jobs.freight_providers.get_quotes", api.jobs.freight_providers.get_quotes(SHIPPING_JOB))
    print(
        json.dumps(
            {
                "quotes": [
                    {"id": str(q.id), "shipping_id": q.shipping_id, "active": q.active, "provider_api": q.provider_api}
                    for q in quotes
                ]
            }
        ),
        flush=True,
    )
    for shipping in before:
        quote = next((q for q in quotes if q.shipping_id == shipping["id"] and q.active), None)
        if quote is not None:
            validation = capture(
                "api.jobs.shipment.validate",
                api.jobs.shipment.validate(
                    SHIPPING_JOB, quote_id=str(quote.id), ship_out_date=datetime.now(timezone.utc) + timedelta(days=1)
                ),
            )
            print(json.dumps({"validation_shipping": shipping["id"], "result": dump(validation)}), flush=True)
    assert dump(api.jobs.shippings.get_all(SHIPPING_JOB)) == before
    print("PASS shipment_validation_preserves_all_shippings", flush=True)
    capture("api.jobs.form.shipments", api.jobs.form.shipments(SHIPPING_JOB))
    print("PASS release_probe_complete", flush=True)


if __name__ == "__main__":
    main()
