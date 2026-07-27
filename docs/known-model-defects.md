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

Add approved values to `examples/constants.py` so examples and tests agree on
one source, then re-run the read-only sweep.

## Environment fault

`tests/helpers/test_timeline_helpers.py` cannot pass at present. Staging returns
**HTTP 500 with an empty body for every timeline task creation** (`pack_start`,
`storage_begin`, and the rest), on a job verified clean: `delete_all` succeeds,
all four task codes read back as absent, and the timeline reports `tasks=[]`
with status "1 - New Job".

This reproduces on an unmodified checkout, so it is neither test pollution nor
an SDK regression — the shared test job is already at its documented baseline.
The suite will pass again when the server-side fault clears; nothing in this
repository can restore it.
