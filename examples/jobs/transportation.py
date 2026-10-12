"""8_01 transportation example; operates on one explicit staging selection.

Set AB_TEST_PACKING_JOB_ID and AB_TEST_SHIPPING_ID to read export data.
To run one write, set AB_RUN_MUTATIONS=1, AB_TRANSPORT_OPERATION and
AB_TRANSPORT_REQUEST (path to an operator-reviewed JSON body). For cancellation
also set AB_TEST_QUOTE_ID. Supported operations: request_rates, select_quote,
validate, book, cancel, save_export. Booking/cancellation have carrier effects.
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
    if os.getenv("AB_TEST_SHIPPING_ID"):
        result = api.jobs.shipment.get_shipping_export_data(job_id, int(os.environ["AB_TEST_SHIPPING_ID"]))
        print(format_result(result))
        if result is not None:
            save("ShippingExportData.json", result)
    if not mutations_enabled():
        return
    operation = os.environ["AB_TRANSPORT_OPERATION"]
    body = json.loads(Path(os.environ["AB_TRANSPORT_REQUEST"]).read_text())
    if operation == "request_rates":
        result = api.jobs.rates.request(job_id, **body)
    elif operation == "select_quote":
        result = api.jobs.rates.select_quote(job_id, **body)
    elif operation == "validate":
        result = api.jobs.shipment.validate(job_id, **body)
    elif operation == "book":
        result = api.jobs.shipment.book_v2(job_id, **body)
    elif operation == "cancel":
        result = api.jobs.shipment.cancel(job_id, os.environ["AB_TEST_QUOTE_ID"], **body)
    elif operation == "save_export":
        result = api.jobs.shipment.save_shipping_export_data(job_id, int(os.environ["AB_TEST_SHIPPING_ID"]), **body)
    else:
        raise ValueError(f"Unknown operation: {operation}")
    print(format_result(result))
    if result is not None:
        save(type(result).__name__ + ".json", result)


if __name__ == "__main__":
    main()
