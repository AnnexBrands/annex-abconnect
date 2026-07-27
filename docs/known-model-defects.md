# Read-only sweep: state of every endpoint

Every routed read-only endpoint is either certified or carries exactly one
explicit blocking state. Blocking reasons are kept distinct on purpose: an
HTTP 401 and an HTTP 500 are not the same problem, and collapsing them into
"failing" hides whether code, fixture data, credentials or staging is
responsible.

## Blocking states

| State | Meaning | Who resolves it |
| --- | --- | --- |
| `certified` | Parses, no undeclared fields, structure matches the fixture. | — |
| `model_defect` | The SDK's declared type disagrees with the wire. | SDK |
| `stale_fixture` | Model is right; the committed fixture predates the response. | Workbench refresh |
| `fixture_collision` | Several endpoints share one fixture filename. | Fixture naming |
| `awaiting_constants` | Request-side: the example has no valid staging identifier. | Operator |
| `authorization_blocked` | HTTP 401 — credentials or scope. | Operator / IT |
| `environment_blocked` | Staging fault. Never an SDK certification failure. | Server team |

## Fixed in this sweep

| Endpoint | Was | Now |
| --- | --- | --- |
| `api.commodities.search` | `Commodity.id: str` | `int` — live returns `1`. Added `code`, `name`, `isActive`, `parentId`, `parentName`, `parentCode`, `parentIsActive`, which were all undeclared. |
| `api.partners.list` | `Partner.id: str` | `int` — live returns `1`. |
| `api.dashboard.get` | `DashboardItem.step: int` | `str` — live sends `"1 "`, `"2 "`, `"2."`, `"10"`. `"2."` does not parse as an integer, so this was never an int arriving as text. |
| `api.views.get_access_info` | `GridViewAccess`, single object | `List[GridViewAccessEntry]`. One class was serving both this GET and the `PUT /views/{viewId}/access` body, so every field the GET returns was undeclared *and* the list response could not validate. Split: `GridViewAccessEntry` is the response, `GridViewAccess` stays the request body. |
| `api.lookup.get_refer_category_hierarchy` | `List[LookupValue]` | `List[ReferCategoryHierarchy]`. Despite living under `/lookup`, it returns a referral record with 21 fields, not the generic `{id, key, name, value}`. |
| `api.documents.list` | — | No SDK change needed: it already returns `list[Document]` correctly. Its *fixture* is a single object. |

Also fixed: `CertificationSession.record_response()` could not serialize a
`List[...]` response — the payload stayed a list of model objects and
`approve_fixture()` failed at the last step of the workflow.

## Still blocked

### `stale_fixture` — awaiting operator approval

Refreshing these means committing values the sanitizer could not classify and
therefore left verbatim. They were inspected and **not** approved:

| Endpoint | Review findings | Why not auto-approved |
| --- | --- | --- |
| `api.companies.get_details` | 16 | A real street address, phone and fax, real revenue figures and contact ids. |
| `api.dashboard.get` | 134 | Real `jobDisplayID` values and job prices. |
| `api.documents.list` | 36 | Filenames embedding real job numbers (`USAR_2000000(2).pdf`). |

The `DashboardSummary` fixture had its `step` values migrated in place from
`int` to `str` to match the corrected model. That is a type migration of
already-sanitized data — no new live data was introduced.

### `fixture_collision` — `LookupValue.json`

More than ten lookup endpoints write the same `LookupValue.json`. Whichever runs
last wins, and every other endpoint then compares against another endpoint's
data. `api.lookup.get_refer_categories` fails for exactly this reason and its
model is correct.

Resolving it needs per-endpoint fixture names, which changes fixture naming
across the lookup group — deliberately not bundled into this sweep.

### `awaiting_constants` — request-side, never guessed at

Inventing an identifier that happens to return 200 would certify an endpoint
against arbitrary data.

| Module | Reason |
| --- | --- |
| `examples.commodities`, `examples.jobs.core` | HTTP 500 |
| `examples.partners`, `examples.documents`, `examples.timeline`, `examples.jobs.payment` | HTTP 404 |
| `examples.contacts_extended` | HTTP 400 — `statuses` must be a non-empty array |
| `examples.lots`, `examples.jobs.shipment` | HTTP 400 — request body |
| `examples.jobs.on_hold` | no on-hold record on the test job |
| `examples.dashboard`, `examples.views`, `examples.commodity_maps`, `examples.companies_extended`, `examples.jobs.feedback` | a *later* call in the module still fails validation; the endpoints fixed above verify individually |

Add approved values to `examples/constants.py` so examples and tests agree on
one source, then re-run the sweep.

### `authorization_blocked`

`examples.rfq` — HTTP 401. Credentials or a scope the current staging user lacks.

### `environment_blocked` — resolved

For a period on 2026-07-26 staging returned HTTP 500 with an empty body for
every timeline task creation, on a job verified clean. It reproduced on an
unmodified checkout and across repeated attempts, so it was not test pollution
or an SDK regression. It cleared on its own with no change on this side;
`tests/helpers/test_timeline_helpers.py` now passes 14/14.

Recorded because a transient 500 on `POST /api/job/{id}/timeline` is worth
knowing about if it recurs — the failing window left no error body and no
correlation id to trace, which is itself worth fixing server-side.
