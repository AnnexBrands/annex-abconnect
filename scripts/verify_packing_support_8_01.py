"""Exercise company packing and editable-form reads; propose sanitized captures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ab import ABConnectAPI
from ab.progress.certify.session import CertificationSession


def main():
    api = ABConnectAPI(env="staging")
    company = "cf8085ed-b2f2-e611-9f52-00155d426802"
    bundle = {}

    def capture(key, result):
        session = CertificationSession(key)
        session.record_response(result)
        session.propose_fixture()
        bundle[session.response_model_name] = {
            "endpoint": key,
            "payload": session.sanitized,
            "review": [d.render() for d in session.sanitize_report.review],
        }
        Path("tests/captures/packing_support.json").write_text(json.dumps(bundle, indent=2) + "\n")
        print(key, "success", getattr(result, "success", None), "extras", list(session.summary.extras), flush=True)
        return result

    item = dict(cPackName="1", sequenceNo=1, quantity=1, length=12, width=10, height=8, weight=4, value=125)
    capture("api.companies.pack_inventories", api.companies.pack_inventories(company, data=[item]))
    result = capture("api.companies.pack_inventory", api.companies.pack_inventory(company, data=item))
    assert result.success
    handling = dict(
        id=1,
        sequenceNo=1,
        inventoryItems=[item],
        contentHandlingUnits=[],
        quantity=1,
        length=12,
        width=10,
        height=8,
        weight=4,
    )
    capture("api.companies.pack_hierarchy", api.companies.pack_hierarchy(company, data=[handling]))
    capture(
        "api.companies.validate_handling_unit",
        api.companies.validate_handling_unit(
            company,
            data={
                "inventoryItemsModel": [item],
                "containerTypeId": 5,
                "containerId": result.data.container_material_id,
                "containerDimensions": {"length": 14, "width": 14, "height": 14},
            },
        ),
    )
    capture(
        "api.companies.get_handling_unit_materials",
        api.companies.get_handling_unit_materials(
            company,
            data={
                "cPackName": "1",
                "containerTypeId": 5,
                "containerId": result.data.container_material_id,
                "length": 12,
                "width": 10,
                "height": 8,
                "weight": 4,
                "value": 125,
            },
        ),
    )
    capture(
        "api.companies.pack_handling_units",
        api.companies.pack_handling_units(
            company,
            data={
                "handlingUnits": [
                    {"id": 1, "quantity": 1, "length": 12, "width": 10, "height": 8}
                ]
            },
        ),
    )
    assert not api.jobs.handling_units.get_all(9165707)
    result = capture("api.jobs.handling_units.manage", api.jobs.handling_units.manage(9165707, handling_units=[]))
    assert result.success and not api.jobs.handling_units.get_all(9165707)
    for key, method in [
        ("invoice_editable", api.jobs.form.invoice_editable),
        ("usar_editable", api.jobs.form.usar_editable),
    ]:
        capture("api.jobs.form." + key, method(5483351))
    print("PASS packing_support_and_editable_forms", flush=True)


if __name__ == "__main__":
    main()
