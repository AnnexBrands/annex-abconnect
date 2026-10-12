"""Cancel the release test shipment; --force-delete explicitly removes only ABConnect state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ab import ABConnectAPI
from ab.progress.certify.session import CertificationSession

force_delete = "--force-delete" in sys.argv
api = ABConnectAPI(env="staging")
job = 5483351
quote_id = "664ee852-119d-4870-7c2f-08df27f6a737"
quotes = api.jobs.freight_providers.get_quotes(job)
target = next(q for q in quotes if str(q.id) == quote_id)
before = [s.model_dump(mode="json") for s in api.jobs.shippings.get_all(job) if s.id != target.shipping_id]
bundle = {}


def capture(key, result):
    s = CertificationSession(key)
    s.record_response(result)
    s.propose_fixture()
    bundle[s.response_model_name] = {
        "endpoint": key,
        "payload": s.sanitized,
        "review": [d.render() for d in s.sanitize_report.review],
    }
    Path("tests/captures/cancellation_forced.json" if force_delete else "tests/captures/cancellation.json").write_text(
        json.dumps(bundle, indent=2) + "\n"
    )
    return result


try:
    shipment = api.shipments.get_shipment(
        franchisee_id="cf8085ed-b2f2-e611-9f52-00155d426802",
        provider_id=str(target.provider_id),
        pro_number=target.pro_number,
    )
    capture("api.shipments.get_shipment", shipment)
    print("carrier_details_captured", flush=True)
except Exception as e:
    print("carrier_details_error", type(e).__name__, getattr(e, "status_code", None), flush=True)
result = capture("api.jobs.shipment.cancel", api.jobs.shipment.cancel(job, quote_id, force_delete=force_delete))
print("cancel", result.success, result.error_message, "override_error", result.override_error, flush=True)
after = [s.model_dump(mode="json") for s in api.jobs.shippings.get_all(job) if s.id != target.shipping_id]
assert before == after
print("PASS cancellation_does_not_change_other_shippings", flush=True)
assert result.success

if force_delete:
    print("ABConnect test shipment removed; carrier cancellation remains unconfirmed", flush=True)
