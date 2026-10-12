"""Read LIVE's staging home grids and summarize candidate 8_01 validation jobs.

Run with staging credentials configured:
    python scripts/discover_staging_jobs.py --company LIVE --scan 10

Only company, job identifiers, and collection counts are printed. No jobs are
mutated, and no response is promoted to a fixture by this discovery script.
"""

from __future__ import annotations

import argparse
import json

from ab import ABConnectAPI


def job_ids(response: object) -> list[int]:
    """Extract job display IDs from the server's LoadResult data rows."""
    rows = response.get("data") if isinstance(response, dict) else response
    if not isinstance(rows, list):
        raise ValueError("Dashboard response has no data array; inspect the server response contract")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected ungrouped dashboard rows")
        values = [v for k, v in row.items() if k.replace("_", "").lower() == "jobdisplayid"]
        if len(values) != 1:
            raise ValueError("Dashboard row must identify exactly one jobDisplayId")
        value = int(values[0])
        if value not in result:
            result.append(value)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", default="LIVE")
    parser.add_argument("--env-file")
    parser.add_argument("--take", type=int, default=100)
    parser.add_argument("--scan", type=int, default=10, help="Inspect up to this many jobs per grid")
    args = parser.parse_args()
    if args.take < 1 or args.scan < 0:
        parser.error("take must be positive and scan must be nonnegative")
    api = ABConnectAPI(env="staging", env_file=args.env_file)
    if api._settings.environment != "staging":
        raise RuntimeError("Discovery requires staging")
    companies = [c for c in api.companies.available_by_current_user() if (c.code or "").upper() == args.company.upper()]
    if len(companies) != 1 or not companies[0].id:
        raise ValueError(f"Expected one accessible company with exact code {args.company!r}")
    company = companies[0]
    print(json.dumps({"environment": "staging", "company": company.code, "company_id": company.id}), flush=True)
    seen = set()
    for name in ["recent_estimates", "inbound", "in_house", "outbound"]:
        response = getattr(api.dashboard, name)(company_id=company.id, take=args.take, require_total_count=True)
        ids = job_ids(response)
        print(
            json.dumps(
                {
                    "grid": name,
                    "total": response.get("totalCount") if isinstance(response, dict) else None,
                    "returned": len(ids),
                    "candidate_job_ids": ids[: args.scan],
                }
            ),
            flush=True,
        )
        for job_id in ids[: args.scan]:
            if job_id in seen:
                continue
            seen.add(job_id)
            inventory = api.jobs.inventory.get_all(job_id)
            units = api.jobs.handling_units.get_all(job_id)
            shippings = api.jobs.shippings.get_all(job_id)
            print(
                json.dumps(
                    {
                        "job_id": job_id,
                        "inventory_count": len(inventory),
                        "handling_unit_count": len(units),
                        "active_shipping_ids": [s.id for s in shippings if s.is_archived is False],
                        "archived_shipping_ids": [s.id for s in shippings if s.is_archived is True],
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
