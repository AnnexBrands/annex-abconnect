"""Create a dedicated staging quote, validate/book/cancel it, and verify isolation.

Uses a new handling unit and shipping record on a disposable LIVE job. Never
selects or cancels an existing quote. Retains marked test records for inspection.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ab import ABConnectAPI
from ab.exceptions import RequestError
from ab.progress.sanitize import sanitize


def dump(value):
    if isinstance(value, list):
        return [dump(x) for x in value]
    return value.model_dump(by_alias=True, mode="json", exclude_unset=True)


def main():
    api = ABConnectAPI(env="staging")
    assert api._settings.environment == "staging"
    job = 5483351
    before = dump(api.jobs.shippings.get_all(job))

    # Legacy rows with NULL CreatedDate are projected with UtcNow on every GET.
    # JobShipmentPlanService.CreateTransportationQuote confirms this fallback.
    def quote_state(rows):
        return [{k: v for k, v in q.items() if k != "createdDate"} for q in dump(rows)]

    old_quotes = quote_state(api.jobs.freight_providers.get_quotes(job))
    original_ids = {s["id"] for s in before}
    captures = {}

    def record(key, result):
        clean, report = sanitize(dump(result))
        captures[key] = {"payload": clean, "review": [d.render() for d in report.review]}
        Path("tests/captures/booking_8_01.json").write_text(json.dumps(captures, indent=2) + "\n")
        return result

    unit = api.jobs.handling_units.create(
        job,
        quantity=1,
        sequence_no=100,
        is_active=True,
        name="SDK 0.3.0 booking isolation",
        length=12,
        width=10,
        height=8,
        weight=4,
        container_type_id=25,
    )
    print("created_test_unit", unit.id, flush=True)
    contacts = api.jobs.shipment.get_origin_destination(job)

    def address(c):
        a = c["address"]
        return {"zipCode": a["zipCode"], "countryId": a["countryId"], "addressLine": a.get("addressLine1")}

    date = datetime.now(timezone.utc) + timedelta(days=2)
    rates = record(
        "api.jobs.rates.request",
        api.jobs.rates.request(
            job,
            ship_out_date=date,
            handling_units=[
                dict(id=unit.id, quantity=1, length=12, width=10, height=8, weight=4, container_type_id=25)
            ],
            origin_address=address(contacts.origin),
            destination_address=address(contacts.destination),
            rate_sources=[3],
            skip_cache=True,
        ),
    )
    assert rates.providers, [e.message for e in rates.errors or []]
    provider = min(rates.providers, key=lambda p: p.net_amount if p.net_amount is not None else float("inf"))
    selection = dict(
        ratesKey=rates.rates_key,
        carrierCode=provider.carrier_code,
        active=True,
        handlingUnits=[dict(id=unit.id, quantity=1)],
    )
    if provider.used_carrier_account_info:
        selection["carrierAccountId"] = provider.used_carrier_account_info.id
    # Refresh-policy routes must reject stale requests even with forceUpdate=true.
    for force in [False, True]:
        try:
            api.jobs.freight_providers.select_rate_quote(
                job, data={**selection, "jobModifiedDate": "2000-01-01T00:00:00Z", "forceUpdate": force}
            )
        except RequestError as exc:
            assert exc.status_code == 400 and "refresh" in exc.message.lower()
        else:
            raise AssertionError("Stale mutation unexpectedly accepted")
        assert dump(api.jobs.shippings.get_all(job)) == before
    print("PASS stale_conflict_preserves_shippings_force_update_cannot_bypass_refresh", flush=True)
    selected = record(
        "api.jobs.freight_providers.select_rate_quote",
        api.jobs.freight_providers.select_rate_quote(job, data=selection),
    )
    assert selected.success, selected.error_message
    quote = selected.transportation_quote
    assert quote and quote.id and quote.shipping_id not in original_ids
    print("created_test_quote", str(quote.id), "shipping", quote.shipping_id, flush=True)
    assert dump([s for s in api.jobs.shippings.get_all(job) if s.id in original_ids]) == before
    current_quotes = {q["id"]: q for q in quote_state(api.jobs.freight_providers.get_quotes(job))}
    for original in old_quotes:
        current = current_quotes[original["id"]]
        changed = [k for k in original if original[k] != current.get(k)]
        print("existing_quote_changes", original["id"], changed, flush=True)
        if changed:
            print(
                "existing_quote_selection",
                original.get("active"),
                current.get("active"),
                original.get("shippingId"),
                current.get("shippingId"),
                flush=True,
            )
        assert not changed, changed
    validation = record(
        "api.jobs.shipment.validate", api.jobs.shipment.validate(job, quote_id=str(quote.id), ship_out_date=date)
    )
    print("booking_validation", validation.valid, [e.message for e in validation.errors or []], flush=True)
    assert validation.valid
    booked = None
    try:
        booked = record(
            "api.jobs.shipment.book_v2", api.jobs.shipment.book_v2(job, quote_id=str(quote.id), ship_out_date=date)
        )
        print("booking_result", booked.success, booked.error_message, flush=True)
        assert booked.success
        assert dump([s for s in api.jobs.shippings.get_all(job) if s.id in original_ids]) == before
        print("PASS explicit_booking_preserves_existing_shipping", flush=True)
    finally:
        cancelled = record("api.jobs.shipment.cancel", api.jobs.shipment.cancel(job, str(quote.id), force_delete=False))
        print("cancellation_result", cancelled.success, cancelled.error_message, flush=True)
        assert cancelled.success
    after_quotes = quote_state(api.jobs.freight_providers.get_quotes(job))
    assert [q for q in after_quotes if q["id"] in {r["id"] for r in old_quotes}] == old_quotes
    assert dump([s for s in api.jobs.shippings.get_all(job) if s.id in original_ids]) == before
    print("PASS booking_cancellation_preserves_other_quotes_and_shippings", flush=True)


if __name__ == "__main__":
    main()
