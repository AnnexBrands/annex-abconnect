"""Verify a targeted export write on an explicitly selected disposable staging shipment.

If the target has no export data, leaves a clearly marked SDK test export record.
Otherwise restores the original export body. Every other shipping/export record
must remain unchanged. Never books or cancels a carrier shipment.
"""

import argparse
import json

from ab import ABConnectAPI
from ab.api.selection import select_shipping


def snapshot(value):
    return None if value is None else value.model_dump(mode="json", by_alias=True, exclude_unset=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=int, required=True)
    parser.add_argument("--shipping-id", type=int, required=True)
    args = parser.parse_args()
    api = ABConnectAPI(env="staging")
    assert api._settings.environment == "staging"
    shippings = api.jobs.shippings.get_all(args.job)
    target = select_shipping(shippings, shipping_id=args.shipping_id)
    assert len([s for s in shippings if s.is_archived is False]) >= 2
    exports = {s.id: api.jobs.shipment.get_shipping_export_data(args.job, s.id) for s in shippings}
    original = exports[target.id]
    body = (
        original.to_request().model_dump(mode="json", by_alias=True, exclude_unset=True)
        if original is not None
        else {"customsValue": 15, "commodities": [], "packingInfo": []}
    )
    body["invoiceNumber"] = "SDK-8_01-ISOLATION-CHECK"
    try:
        api.jobs.shipment.save_shipping_export_data(args.job, target.id, **body)
        result = api.jobs.shipment.get_shipping_export_data(args.job, target.id)
        assert result is not None and result.invoice_number == body["invoiceNumber"]
        for shipping in shippings:
            if shipping.id != target.id:
                actual = api.jobs.shipment.get_shipping_export_data(args.job, shipping.id)
                assert snapshot(actual) == snapshot(exports[shipping.id])
        assert [snapshot(s) for s in api.jobs.shippings.get_all(args.job)] == [snapshot(s) for s in shippings]
        print(
            json.dumps(
                {
                    "check": "targeted_export_write_preserves_other_shippings",
                    "result": "passed",
                    "job": args.job,
                    "shipping_id": target.id,
                    "unaffected_shipping_ids": [s.id for s in shippings if s.id != target.id],
                }
            ),
            flush=True,
        )
    finally:
        if original is not None:
            restore = original.to_request().model_dump(mode="json", by_alias=True, exclude_unset=True)
            api.jobs.shipment.save_shipping_export_data(args.job, target.id, **restore)
            assert snapshot(api.jobs.shipment.get_shipping_export_data(args.job, target.id)) == snapshot(original)
            print(json.dumps({"target_export_restored": True}), flush=True)
        else:
            print(
                json.dumps(
                    {
                        "target_export_restored": False,
                        "reason": "No export-delete endpoint; SDK test record retained",
                        "job": args.job,
                        "shipping_id": target.id,
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
