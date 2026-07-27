# Known model defects and blocked endpoints

Findings from the read-only certification sweep. Each entry is a mismatch
between a declared model and what staging actually returns, observed live and
reproduced through the shared comparator
(`ab.progress.compare`). Nothing here is speculative — every row was seen on a
real response.

Recorded rather than fixed in the same change: correcting a declared type
changes the SDK's public surface, and each needs its own decision about whether
the model or the API is wrong.

## Confirmed model defects

| Endpoint | Path | Declared | Observed live | Notes |
| --- | --- | --- | --- | --- |
| `api.commodities.search` | `Commodity.id` | `str` | `1` (int) | Integer primary key returned where a string is declared. |
| `api.partners.list` | `Partner.id` | `str` | `1` (int) | Same shape of defect as `Commodity.id`. |
| `api.dashboard.get_grid_views` | `DashboardSummary.data[].step` | `int` | `"2."` (str) | Not merely a string — `"2."` does not parse as an integer, so widening to `int \| str` is not enough on its own; the trailing dot needs a decision. |
| `api.views.get_access_info` | `GridViewAccess` | object | `[{...}]` (list) | The endpoint returns a collection; the route/model expects a single object. Needs a list wrapper, not a field type change. |
| `api.documents.list` | root | object | list | Same shape of defect as `GridViewAccess`, found once the comparator stopped drowning in false failures. |

## Stale fixtures

Live responses carry fields the committed fixture predates. These are not model
defects — the SDK parses them — but the fixture no longer represents the
endpoint. Refresh each through the workbench so the new fields are sanitized and
approved rather than captured raw.

| Endpoint | Fields live-only |
| --- | --- |
| `api.companies.get_details` | `addresses`, `contacts`, `settings` |
| `api.lookup.get_refer_categories` | 12 fields incl. `actionType`, `companyID`, `contactID`, `directEmail`, `landingUrl` |
| `api.lookup.get_refer_category_hierarchy` | same 12 fields |

Each is covered by a regression test in `tests/test_compare.py`, so whichever
way they are resolved, the comparator keeps proving it can still tell this class
of drift from sanitized-value noise.

## Blocked pending approved operator constants

These modules raise before producing a response. The failures are request-side —
stale or missing identifiers — not model defects. They are deliberately **not**
guessed at: inventing an id that happens to return 200 would certify the
endpoint against arbitrary data.

| Module | Status | Needs |
| --- | --- | --- |
| `examples.companies` | HTTP 500 | A valid staging company id. |
| `examples.jobs.core` | HTTP 500 | A valid staging job. |
| `examples.documents` | HTTP 404 | A job with a document attached. |
| `examples.timeline` | HTTP 404 | A job whose timeline exists. |
| `examples.lots` | HTTP 400 | A valid lot request body. |
| `examples.contacts_extended` | HTTP 400 | `statuses` must be a non-empty array. |
| `examples.rfq` | HTTP 401 | Credentials or a scope the current staging user lacks. |
| `examples.commodities`, `examples.commodity_maps`, `examples.partners`, `examples.dashboard`, `examples.views` | model validation | Blocked by the confirmed defects above, not by data. |
| `examples.contacts`, `examples.companies_extended`, `examples.jobs.feedback`, `examples.jobs.on_hold`, `examples.jobs.payment`, `examples.jobs.shipment` | raises | Needs a staging record the current constants do not point at. |

Add approved values to `examples/constants.py` so examples and tests agree on
one source, then re-run the read-only sweep.

## Environment: resolved (transient staging fault)

For a period on 2026-07-26, staging returned **HTTP 500 with an empty body for
every timeline task creation** (`pack_start`, `storage_begin`), on a job verified
clean — `delete_all` succeeded, all four task codes read back absent, the
timeline reported `tasks=[]` at status "1 - New Job". It reproduced on an
unmodified checkout and across repeated attempts, so it was not test pollution
or an SDK regression.

It has since cleared on its own, from the same baseline and the same call, with
no change on this side: `tests/helpers/test_timeline_helpers.py` passes 14/14.
Recorded because a transient 500 on `POST /api/job/{id}/timeline` is worth
knowing about if it recurs — the failing window left no error body and no
correlation id to trace, which is itself worth fixing server-side.

**Classification: `environment_blocked` while it lasts, never SDK certification
failure.** Nothing in this repository can restore staging, and a red suite for
this reason must not be read as the SDK being wrong.
