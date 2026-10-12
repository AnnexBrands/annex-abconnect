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
    result = api.jobs.inventory.get_all(job_id)
    print(format_result(result))
    if result:
        save("JobInventoryItem.json", result[0])
    if not mutations_enabled():
        return
    operation = os.environ["AB_PACKING_OPERATION"]
    body = json.loads(Path(os.environ["AB_PACKING_REQUEST"]).read_text())
    if operation == "create":
        result = api.jobs.inventory.create(
            job_id,
            **body,
        )
    elif operation == "update":
        result = api.jobs.inventory.update(
            job_id,
            int(os.environ["AB_TEST_INVENTORY_ITEM_ID"]),
            **body,
        )
    elif operation == "delete":
        result = api.jobs.inventory.delete(
            job_id,
            int(os.environ["AB_TEST_INVENTORY_ITEM_ID"]),
        )
    else:
        raise ValueError(f"Unknown operation: {operation}")
    print(format_result(result))


if __name__ == "__main__":
    main()
