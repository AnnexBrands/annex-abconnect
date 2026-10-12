"""Read current staging quote/packing metadata and request rates without booking."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ab import ABConnectAPI
from ab.exceptions import RequestError
from ab.progress.sanitize import sanitize

api = ABConnectAPI(env="staging")
company = "cf8085ed-b2f2-e611-9f52-00155d426802"
groups = api.lookup.get_container_types(company_id=company)
cpacks = api.lookup.get_cpacks()
print(
    "container_types",
    [
        {"group": g.name, "types": [{"id": t.id, "code": t.code, "name": t.name} for t in g.container_types or []]}
        for g in groups
    ],
    flush=True,
)
print("cpacks", [c.name for c in cpacks], flush=True)
box = next(t for g in groups for t in (g.container_types or []) if t.is_active and t.code == "BOXES")
pack = api.companies.pack_inventory(
    company,
    data={
        "cPackName": cpacks[0].name,
        "sequenceNo": 1,
        "quantity": 1,
        "length": 12,
        "width": 10,
        "height": 8,
        "weight": 4,
        "value": 125,
    },
)
clean, report = sanitize(pack.model_dump(by_alias=True, mode="json", exclude_unset=True))
Path("tests/captures/pack_probe.json").write_text(
    json.dumps({"response": clean, "review": [d.render() for d in report.review]}, indent=2)
)
print("pack_result", pack.success, flush=True)
for job in [5483351]:
    units = api.jobs.handling_units.get_all(job)
    quotes = api.jobs.freight_providers.get_quotes(job)
    print(
        json.dumps(
            {
                "job": job,
                "units": [
                    {
                        "id": u.id,
                        "cpack": u.c_pack_id if hasattr(u, "c_pack_id") else None,
                        "length": u.length,
                        "width": u.width,
                        "height": u.height,
                        "weight": u.weight,
                    }
                    for u in units
                ],
                "quotes": [
                    {"id": str(q.id), "shipping": q.shipping_id, "active": q.active, "provider_api": q.provider_api}
                    for q in quotes
                ],
            }
        ),
        flush=True,
    )
    origin = api.jobs.shipment.get_origin_destination(job)
    print(
        "origin_destination_keys",
        job,
        {
            k: list(v) if isinstance(v, dict) else type(v).__name__
            for k, v in origin.model_dump(by_alias=True, exclude_none=True).items()
        },
        flush=True,
    )
    if job != 5483351:
        continue
    body = dict(
        ship_out_date=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        handling_units=[
            dict(id=units[0].id, quantity=1, length=12, width=10, height=8, weight=4, container_type_id=box.id)
        ],
        origin_address={
            "zipCode": origin.origin["address"]["zipCode"],
            "countryId": origin.origin["address"]["countryId"],
        },
        destination_address={
            "zipCode": origin.destination["address"]["zipCode"],
            "countryId": origin.destination["address"]["countryId"],
        },
        skip_cache=True,
        rate_sources=[3],
    )
    try:
        rates = api.jobs.rates.request(job, **body)
        payload = rates.model_dump(by_alias=True, mode="json", exclude_unset=True)
        clean, report = sanitize(payload)
        Path("tests/captures/rates_probe.json").write_text(
            json.dumps(
                {"job": job, "request": body, "response": clean, "review": [d.render() for d in report.review]},
                indent=2,
            )
        )
        print(
            "rate_result",
            list(payload),
            "review",
            len(report.review),
            "errors",
            [e.message for e in rates.errors or []],
            flush=True,
        )
        print(
            "rate_counts",
            {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in payload.items()},
            flush=True,
        )
    except RequestError as e:
        print("rate_error", e.status_code, e.message[:500], flush=True)
