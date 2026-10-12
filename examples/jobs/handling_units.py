"""8_01 packing example using operator-selected staging records.

Set AB_TEST_PACKING_JOB_ID. Reads are the default. To exercise one mutation,
set AB_RUN_MUTATIONS=1, AB_PACKING_OPERATION to the method name, and
AB_PACKING_REQUEST to a JSON file containing that method's request body.
Set AB_TEST_HANDLING_UNIT_ID / AB_TEST_INVENTORY_ITEM_ID / AB_TEST_MATERIAL_ID
or AB_TEST_CONTENT_UNIT_ID where the operation needs an existing child record.
Never use a customer's production job for mutation examples.
"""

import json
import os
from pathlib import Path

from ab import ABConnectAPI
from ab.cli.formatter import format_result
from examples._capture import mutations_enabled, save


def main() -> None:
    job_id = int(os.environ["AB_TEST_PACKING_JOB_ID"])
    api = ABConnectAPI(env="staging")
    result = api.jobs.handling_units.get_all(job_id)
    print(format_result(result))
    if result:
        save("JobHandlingUnitDetails.json", result[0])
    if os.getenv("AB_TEST_HANDLING_UNIT_ID"):
        materials = api.jobs.handling_units.get_materials(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
        )
        print(format_result(materials))
        if materials:
            save("HandlingUnitMaterial.json", materials[0])
    if not mutations_enabled():
        return
    operation = os.environ["AB_PACKING_OPERATION"]
    body = json.loads(Path(os.environ["AB_PACKING_REQUEST"]).read_text())
    if operation == "create":
        result = api.jobs.handling_units.create(
            job_id,
            **body,
        )
    elif operation == "manage":
        result = api.jobs.handling_units.manage(
            job_id,
            **body,
        )
    elif operation == "update":
        result = api.jobs.handling_units.update(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            **body,
        )
    elif operation == "delete":
        result = api.jobs.handling_units.delete(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
        )
    elif operation == "add_inventory":
        result = api.jobs.handling_units.add_inventory(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            data=body,
        )
    elif operation == "update_inventory":
        result = api.jobs.handling_units.update_inventory(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_INVENTORY_ITEM_ID"]),
            **body,
        )
    elif operation == "delete_inventory":
        result = api.jobs.handling_units.delete_inventory(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_INVENTORY_ITEM_ID"]),
        )
    elif operation == "add_content_units":
        result = api.jobs.handling_units.add_content_units(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            data=body,
        )
    elif operation == "update_content_unit":
        result = api.jobs.handling_units.update_content_unit(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_CONTENT_UNIT_ID"]),
            **body,
        )
    elif operation == "delete_content_unit":
        result = api.jobs.handling_units.delete_content_unit(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_CONTENT_UNIT_ID"]),
        )
    elif operation == "add_materials":
        result = api.jobs.handling_units.add_materials(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            data=body,
        )
    elif operation == "replace_materials":
        result = api.jobs.handling_units.replace_materials(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            data=body,
        )
    elif operation == "set_container_material":
        result = api.jobs.handling_units.set_container_material(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            **body,
        )
    elif operation == "update_material":
        result = api.jobs.handling_units.update_material(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_MATERIAL_ID"]),
            **body,
        )
    elif operation == "delete_material":
        result = api.jobs.handling_units.delete_material(
            job_id,
            int(os.environ["AB_TEST_HANDLING_UNIT_ID"]),
            int(os.environ["AB_TEST_MATERIAL_ID"]),
        )
    else:
        raise ValueError(f"Unknown operation: {operation}")
    print(format_result(result))


if __name__ == "__main__":
    main()
